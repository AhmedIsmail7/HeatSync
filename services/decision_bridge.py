"""FortyGuard Decision Engine Integration Bridge.

Defines schemas and adapter methods to translate external Decision Engine
and FortyGuard API JSON payloads directly into standardized UI models.
"""

from typing import Any, Dict, List, Optional
import pandas as pd


class DecisionBridge:
    @staticmethod
    def parse_api_environmental_payload(payload: Dict[str, Any]) -> pd.DataFrame:
        """Parse raw environmental forecast payload from FortyGuard API (/v1/env_params)
        into normalized DataFrame.
        """
        hourly_data = payload.get("forecast", [])
        if not hourly_data:
            return pd.DataFrame()
            
        df = pd.DataFrame(hourly_data)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    @staticmethod
    def parse_decision_engine_output(engine_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LangChain / LangGraph output payload from Decision Engine (Ahmed)
        into structured UI model.
        """
        return {
            "recommended_mode": engine_result.get("recommended_mode", "Free-Air Cooling"),
            "ashrae_compliance": engine_result.get("ashrae_compliance", "ASHRAE A1 Recommended"),
            "pue_delta": engine_result.get("pue_delta", -0.22),
            "hourly_cost_savings": engine_result.get("hourly_cost_savings_usd", 185.0),
            "risk_level": engine_result.get("risk_level", "Safe"),
            "narrative": engine_result.get("llm_narrative", ""),
            "alerts": engine_result.get("alerts", []),
        }
