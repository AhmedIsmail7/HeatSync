"""
HeatSync Data Pipeline
======================
Central ingestion engine for facility environmental data.

Provides:
  - ``FACILITY_REGISTRY``: Canonical metadata for all monitored data-center sites.
  - ``create_aoi_polygon()``: GeoJSON bounding-box generator for FortyGuard queries.
  - ``normalize_env_params()``: Raw API JSON → clean Pandas DataFrame with
    standardized column names matching downstream schema expectations.
  - ``fetch_facility_data()``: Cache-first data loader with optional live API fetch.
  - ``load_facility_json()`` / ``list_available_facilities()``: Backward-compatible
    helpers used by orchestration_graph, comparison_engine, and pipeline modules.
"""

import json
import logging
import os
import datetime
from typing import Any, Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ---------------------------------------------------------------------------
# Facility Registry
# ---------------------------------------------------------------------------
FACILITY_REGISTRY: Dict[str, Dict[str, Any]] = {
    "ASHBURN": {
        "id": "ASHBURN",
        "name": "Ashburn DC-1 (Equinix Hub)",
        "location": "Ashburn, VA",
        "lat": 39.0437,
        "lon": -77.4875,
        "it_load_mw": 10.0,
        "utility_rate_kwh": 0.085,
        "electricity_rate_kwh": 0.085,
        "baseline_pue": 1.55,
    },
    "PHOENIX": {
        "id": "PHOENIX",
        "name": "Phoenix DC-2 (Desert Hub)",
        "location": "Phoenix, AZ",
        "lat": 33.4484,
        "lon": -112.0740,
        "it_load_mw": 15.0,
        "utility_rate_kwh": 0.095,
        "electricity_rate_kwh": 0.095,
        "baseline_pue": 1.55,
    },
    "SANJOSE": {
        "id": "SANJOSE",
        "name": "San José DC-3 (Silicon Valley)",
        "location": "San José, CA",
        "lat": 37.3382,
        "lon": -121.8863,
        "it_load_mw": 8.0,
        "utility_rate_kwh": 0.145,
        "electricity_rate_kwh": 0.145,
        "baseline_pue": 1.55,
    },
}

# ---------------------------------------------------------------------------
# GeoJSON AOI helper
# ---------------------------------------------------------------------------

def create_aoi_polygon(lat: float, lon: float, delta: float = 0.015) -> dict:
    """
    Build a GeoJSON FeatureCollection with a single rectangular Polygon
    centered on *(lat, lon)* ± *delta* degrees.

    The polygon is a closed ring of 5 coordinate pairs (first == last).

    Returns:
        dict: A valid GeoJSON FeatureCollection.
    """
    sw = [lon - delta, lat - delta]
    nw = [lon - delta, lat + delta]
    ne = [lon + delta, lat + delta]
    se = [lon + delta, lat - delta]
    ring = [sw, nw, ne, se, sw]  # closed polygon

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [ring],
                },
                "properties": {},
            }
        ],
    }


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

# Column mapping: raw FortyGuard key → canonical downstream name
_RAW_TO_CANONICAL = {
    "apparent_temperature_celsius": "apparent_temperature_celsius",
    "wet_bulb_temperature_celsius": "wet_bulb_temperature_celsius",
    "heat_index_celsius": "heat_index_celsius",
    "relative_humidity_percent": "relative_humidity_percent",
    "air_quality_pm2p5_idx": "air_quality_pm2p5_idx",
    "air_quality_pm10_idx": "air_quality_pm10_idx",
    "air_quality_no2_idx": "air_quality_no2_idx",
    "air_quality_so2_idx": "air_quality_so2_idx",
    "air_quality_o3_idx": "air_quality_o3_idx",
    "aqi_us_co": "aqi_us_co",
    "co2_ppm": "co2_ppm",
    "methane_ppb": "methane_ppb",
    "cloud_cover_octas": "cloud_cover_octas",
    "precipitation_mm": "precipitation_mm",
}

# Fallback defaults for optional keys that downstream code may reference.
_DEFAULTS: Dict[str, float] = {
    "heat_index_celsius": 0.0,
    "relative_humidity_percent": 50.0,
    "air_quality_pm2p5_idx": 25.0,
    "air_quality_pm10_idx": 10.0,
    "air_quality_no2_idx": 5.0,
    "air_quality_so2_idx": 0.5,
    "air_quality_o3_idx": 20.0,
    "aqi_us_co": 1.0,
    "co2_ppm": 420.0,
    "methane_ppb": 1900.0,
    "cloud_cover_octas": 0.0,
    "precipitation_mm": 0.0,
}


def normalize_env_params(raw_json: dict) -> pd.DataFrame:
    """
    Transform a raw FortyGuard ``env_params`` response (or cached JSON) into
    a clean :class:`~pandas.DataFrame` with:

    * 24 rows (hours 0–23)
    * Standardized column names matching downstream schema
    * Alias columns: ``T_apparent``, ``T_wb``, ``RH``, ``pm25``
    * Solar irradiance columns (``ghi``, ``dni``, ``dhi``) broadcast from
      location metadata when available
    * Fallback defaults for any missing optional atmospheric/pollutant keys

    Args:
        raw_json: Full JSON payload containing ``"hourly_records"`` (list of
            dicts) and optionally ``"location"`` metadata.

    Returns:
        pd.DataFrame with one row per hour and all required columns.
    """
    if "hourly_records" in raw_json:
        records = raw_json["hourly_records"]
        if not records:
            raise ValueError("Raw JSON contains no 'hourly_records'.")
        df = pd.DataFrame(records)
        location = raw_json.get("location", {})
        solar = location.get("solar_irradiance", {})
    elif "locations" in raw_json and len(raw_json["locations"]) > 0:
        loc = raw_json["locations"][0]
        params = loc.get("parameters", {})
        df = pd.DataFrame(params)
        
        # Parse timestamps if available
        if "metadata" in raw_json and "timestamps" in raw_json["metadata"]:
            df["timestamp"] = raw_json["metadata"]["timestamps"]
            # Extract just HH:MM
            df["timestamp"] = df["timestamp"].apply(lambda t: t.split("T")[1][:5] if "T" in str(t) else t)
            
        # Rename any odd keys if necessary
        rename_map = {
            "air_quality:idx": "air_quality_idx",
            "air_quality_pm2p5:idx": "air_quality_pm2p5_idx",
            "air_quality_pm10:idx": "air_quality_pm10_idx",
            "air_quality_no2:idx": "air_quality_no2_idx",
            "air_quality_o3:idx": "air_quality_o3_idx",
            "air_quality_so2:idx": "air_quality_so2_idx",
        }
        df.rename(columns=rename_map, inplace=True)
        
        solar = loc.get("solar_irradiance", {}).get("clear_sky", {})
    else:
        raise ValueError("Raw JSON does not match expected v1 schema.")

    # --- Extract hour from timestamp string "HH:MM" ------------------
    if "timestamp" in df.columns:
        df["hour"] = df["timestamp"].apply(lambda t: int(str(t).split(":")[0]))
    else:
        df["hour"] = range(len(df))

    # --- Synthesize 24-hour diurnal curve if API returned 1 row ---
    if len(df) == 1:
        import math
        base_row = df.iloc[0].to_dict()
        base_hour = base_row.get("hour", 12)
        
        rows = []
        for h in range(24):
            new_row = base_row.copy()
            new_row["hour"] = h
            
            # Simple diurnal math: temperature peaks at 15:00, lowest at 03:00.
            # Max swing +/- 5 degrees C from the base.
            hour_diff = h - 15
            temp_swing = 5.0 * math.cos(hour_diff * math.pi / 12.0)
            base_swing = 5.0 * math.cos((base_hour - 15) * math.pi / 12.0)
            
            if "apparent_temperature_celsius" in new_row:
                true_mean = new_row["apparent_temperature_celsius"] - base_swing
                new_row["apparent_temperature_celsius"] = true_mean + temp_swing
                
            if "wet_bulb_temperature_celsius" in new_row:
                true_mean = new_row["wet_bulb_temperature_celsius"] - (base_swing * 0.7)
                new_row["wet_bulb_temperature_celsius"] = true_mean + (temp_swing * 0.7)
                
            if "relative_humidity_percent" in new_row:
                true_mean = new_row["relative_humidity_percent"] + (base_swing * 2.0)
                new_row["relative_humidity_percent"] = max(10.0, min(100.0, true_mean - (temp_swing * 2.0)))
                
            rows.append(new_row)
            
        df = pd.DataFrame(rows)

    # --- Apply fallback defaults for missing columns ------------------
    for col, default in _DEFAULTS.items():
        if col not in df.columns:
            df[col] = default
    df.fillna(value=_DEFAULTS, inplace=True)

    # --- Solar irradiance from location metadata ----------------------
    for key in ("ghi", "dni", "dhi"):
        if key not in df.columns:
            df[key] = solar.get(key, 0.0)

    # --- Convenience alias columns ------------------------------------
    df["T_apparent"] = df["apparent_temperature_celsius"]
    df["T_wb"] = df["wet_bulb_temperature_celsius"]
    df["RH"] = df["relative_humidity_percent"]
    df["pm25"] = df["air_quality_pm2p5_idx"]

    return df


# ---------------------------------------------------------------------------
# Data fetching (cache-first, optional live)
# ---------------------------------------------------------------------------

def fetch_facility_data(
    facility_id: str,
    date_str: str = None,
    time_str: str = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Load environmental data for a facility.

    Strategy:
      1. If a cache file exists **and** (``use_cache=True`` or no API key),
         return the cached + normalized DataFrame.
      2. Otherwise call FortyGuard live, persist the response to cache, and
         return the normalized DataFrame.

    Args:
        facility_id: Registry key (e.g. ``"ASHBURN"``).
        date_str: Date for the API query (ISO-8601, default ``"2024-07-15"``).
        time_str: Start time for the API query (default ``"14:00"``).
        use_cache: If ``True`` and cache exists, prefer cache over live fetch.

    Returns:
        pd.DataFrame: Normalized hourly environmental data.
    """
    fid_upper = facility_id.upper()
    fid_lower = facility_id.lower()
    if date_str is None or time_str is None:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        if date_str is None:
            date_str = now_utc.strftime("%Y-%m-%d")
        if time_str is None:
            time_str = now_utc.strftime("%H:00")
        
    # We still use a cache file, but we will scope it to the date to ensure fresh daily data
    cache_path = os.path.join(DATA_DIR, f"{fid_lower}_env_{date_str}.json")
    api_key = os.environ.get("FORTYGUARD_API_KEY")

    # --- Cache path -------------------------------------------------
    cache_exists = os.path.isfile(cache_path)

    if cache_exists and (use_cache or not api_key):
        logger.info("Loading cached data for %s from %s", fid_upper, cache_path)
        with open(cache_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return normalize_env_params(raw)

    # --- Live fetch -------------------------------------------------
    if not api_key:
        raise RuntimeError(
            f"No cache found for '{fid_upper}' and FORTYGUARD_API_KEY is not set."
        )

    if fid_upper not in FACILITY_REGISTRY:
        raise KeyError(f"Facility '{fid_upper}' not found in FACILITY_REGISTRY.")

    reg = FACILITY_REGISTRY[fid_upper]
    payload = {
        "latitude": reg["lat"],
        "longitude": reg["lon"],
        "temperature": 32.5,
        "date_time": {
            "start_date": date_str,
            "start_time": time_str,
            "filter_type": 1
        }
    }

    # Import here to avoid circular dependency at module level
    from fortyguard_client import FortyGuardClient  # noqa: E402

    client = FortyGuardClient(api_key=api_key)
    raw_result = client.get_env_params_sync(payload)

    # Persist to cache
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(raw_result, f, indent=2)
    logger.info("Saved live response to cache: %s", cache_path)

    return normalize_env_params(raw_result)


# ---------------------------------------------------------------------------
# Backward-compatible public API
# ---------------------------------------------------------------------------

def list_available_facilities() -> list:
    """Return all canonical facility names registered in the system."""
    return [meta["id"].lower() for meta in FACILITY_REGISTRY.values()]


def load_facility_json(facility_name: str = "ashburn") -> tuple:
    """
    Load a cached facility JSON and return *(meta_dict, DataFrame)*.

    This preserves the exact contract expected by
    :pyfunc:`orchestration_graph.node_ingest_data` and
    :pyfunc:`comparison_engine.compare_all_facilities`.
    """
    filepath = os.path.join(DATA_DIR, f"{facility_name}_env.json")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Missing dataset: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        payload = json.load(f)

    meta = dict(payload.get("location", {}))
    
    # Merge with canonical FACILITY_REGISTRY if available
    fid_upper = facility_name.upper().replace("-VA", "").replace("-AZ", "").replace("-CA", "")
    if fid_upper in FACILITY_REGISTRY:
        meta = {**FACILITY_REGISTRY[fid_upper], **meta}

    # Guarantee all standard alias keys exist
    if "utility_rate_kwh" not in meta and "electricity_rate_kwh" in meta:
        meta["utility_rate_kwh"] = meta["electricity_rate_kwh"]
    if "electricity_rate_kwh" not in meta and "utility_rate_kwh" in meta:
        meta["electricity_rate_kwh"] = meta["utility_rate_kwh"]
    if "location" not in meta:
        meta["location"] = meta.get("name", f"{facility_name.title()}, USA")
    if "baseline_pue" not in meta:
        meta["baseline_pue"] = 1.55

    df = pd.DataFrame(payload["hourly_records"])

    # Extract integer hour from "HH:MM" → int
    df["hour"] = df["timestamp"].apply(lambda t: int(t.split(":")[0]))

    return meta, df