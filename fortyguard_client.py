"""
FortyGuard API Client
=====================
Robust HTTP client wrapping FortyGuard's environmental intelligence endpoints.
Implements exponential-backoff polling for async job completion and quota tracking.
"""

import os
import time
import logging
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class FortyGuardClient:
    """
    Client for the FortyGuard Environmental Intelligence API.

    Supports:
      - Submitting env_params, heatmap, and heat_intelligence jobs.
      - Polling job status with configurable exponential backoff.
      - Fetching API key usage / quota information.

    Usage::

        client = FortyGuardClient(api_key="your-key")
        result = client.get_env_params_sync(payload)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.fortyguard.com",
        timeout: int = 15,
    ):
        self.api_key = api_key or os.environ.get("FORTYGUARD_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        if self.api_key:
            self._session.headers["api-key"] = self.api_key

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _post(self, path: str, json_body: Optional[dict] = None) -> Dict[str, Any]:
        """Execute a POST request and return the parsed JSON response."""
        url = f"{self.base_url}{path}"
        logger.debug("POST %s", url)
        resp = self._session.post(url, json=json_body, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def _get(self, path: str) -> Dict[str, Any]:
        """Execute a GET request and return the parsed JSON response."""
        url = f"{self.base_url}{path}"
        logger.debug("GET %s", url)
        resp = self._session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Public endpoint methods
    # ------------------------------------------------------------------

    def fetch_api_usage(self) -> Dict[str, Any]:
        """
        Retrieve current API key usage and quota information.

        Returns:
            dict with usage stats (calls remaining, rate limits, etc.)
        """
        return self._post("/v1/system/fetch-api-key-usage")

    def submit_env_params(self, payload: dict) -> str:
        """
        Submit an environmental-parameters job.

        Args:
            payload: Request body matching FortyGuard's /v1/env_params schema.

        Returns:
            The ``activity_id`` for polling.
        """
        data = self._post("/v1/env_params", json_body=payload)
        return data.get("data", {}).get("activity_id", data.get("activity_id"))

    def submit_heatmap(self, payload: dict) -> str:
        """
        Submit a heatmap generation job.

        Args:
            payload: Request body matching FortyGuard's /v1/heatmap schema.

        Returns:
            The ``activity_id`` for polling.
        """
        data = self._post("/v1/heatmap", json_body=payload)
        return data.get("data", {}).get("activity_id", data.get("activity_id"))

    def submit_heat_intelligence(self, payload: dict) -> str:
        """
        Submit a heat-intelligence analysis job.

        Args:
            payload: Request body matching FortyGuard's /v1/heat_intelligence schema.

        Returns:
            The ``activity_id`` for polling.
        """
        data = self._post("/v1/heat_intelligence", json_body=payload)
        return data.get("data", {}).get("activity_id", data.get("activity_id"))

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    def poll_status(
        self,
        activity_id: str,
        max_retries: int = 5,
        initial_wait: float = 1.0,
        max_wait: float = 10.0,
        backoff_factor: float = 1.5,
    ) -> Dict[str, Any]:
        """
        Poll ``GET /v1/status/{activity_id}`` with exponential backoff until
        the job completes, fails, or retries are exhausted.

        Args:
            activity_id: Job identifier returned by a submit method.
            max_retries: Maximum number of polling attempts.
            initial_wait: Seconds to wait before the first retry.
            max_wait: Cap on the backoff delay (seconds).
            backoff_factor: Multiplier applied each iteration.

        Returns:
            The ``result`` payload from the completed job.

        Raises:
            RuntimeError: If the job status is ``"Failed"`` or retries are
                          exhausted without completion.
        """
        for attempt in range(max_retries):
            data = self._get(f"/v1/status/{activity_id}")
            inner_data = data.get("data", data)
            status = inner_data.get("status", data.get("status", "")).strip()

            if status == "Completed":
                logger.info(
                    "Job %s completed on attempt %d", activity_id, attempt + 1
                )
                return inner_data.get("result", inner_data)

            if status == "Failed":
                error_msg = data.get("error", "Unknown error")
                raise RuntimeError(
                    f"FortyGuard job {activity_id} failed: {error_msg}"
                )

            if status in ("Processing", "Pending"):
                wait = min(initial_wait * (backoff_factor ** attempt), max_wait)
                logger.debug(
                    "Job %s status=%s, waiting %.1fs (attempt %d/%d)",
                    activity_id,
                    status,
                    wait,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(wait)
            else:
                # Unexpected status — treat as transient, keep polling
                wait = min(initial_wait * (backoff_factor ** attempt), max_wait)
                logger.warning(
                    "Unexpected status '%s' for job %s, retrying in %.1fs",
                    status,
                    activity_id,
                    wait,
                )
                time.sleep(wait)

        raise RuntimeError(
            f"FortyGuard job {activity_id} did not complete after "
            f"{max_retries} polling attempts."
        )

    # ------------------------------------------------------------------
    # Convenience sync wrappers
    # ------------------------------------------------------------------

    def get_env_params_sync(self, payload: dict, **poll_kwargs) -> Dict[str, Any]:
        """Submit an env_params job and block until the result is ready."""
        activity_id = self.submit_env_params(payload)
        return self.poll_status(activity_id, **poll_kwargs)

    def get_heatmap_sync(self, payload: dict, **poll_kwargs) -> Dict[str, Any]:
        """Submit a heatmap job and block until the result is ready."""
        activity_id = self.submit_heatmap(payload)
        return self.poll_status(activity_id, **poll_kwargs)
