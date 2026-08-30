"""FortyGuard / HeatSync Data Service Layer.

Directly bridges the LangGraph Orchestration Pipeline (Ahmed),
FortyGuard Ingestion & Caching Layer (David), and the Streamlit UI (Ramy).
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

from data_pipeline import (
    FACILITY_REGISTRY,
    list_available_facilities,
    load_facility_json,
)
from cooling_engine import apply_cooling_rules
from efficiency_model import compute_energy_metrics, generate_kpi_summary
from alert_engine import scan_forecast_alerts
from comparison_engine import compare_all_facilities
from pipeline import get_heat_sync_analytics
from utils.helpers import calculate_wet_bulb, calculate_dew_point


class DataService:
    def __init__(self, mode: str = "pipeline"):
        self.mode = mode

    def get_facility_list(self) -> List[Dict[str, Any]]:
        """Return canonical metadata list for all registered facilities."""
        facilities = []
        for key, meta in FACILITY_REGISTRY.items():
            facilities.append({
                "id": meta["id"].lower(),
                "key": meta["id"],
                "name": meta["name"],
                "city": meta["location"],
                "lat": meta["lat"],
                "lon": meta["lon"],
                "it_load_mw": meta["it_load_mw"],
                "baseline_pue": meta["baseline_pue"],
                "electricity_cost_kwh": meta["utility_rate_kwh"],
                "status": "Operational" if meta["id"] != "PHOENIX" else "Thermal Stress Warning",
                "current_active_mode": "Free-Air Economizer" if meta["id"] == "SANJOSE" else ("Direct Evaporative" if meta["id"] == "ASHBURN" else "Mechanical Chiller (DX)"),
                "cooling_infrastructure": "Indirect/Direct Economizer + Adiabatic Trim & Backup DX Chillers",
            })
        return facilities

    def get_facility_by_id(self, facility_id: str) -> Dict[str, Any]:
        """Fetch metadata for a given facility."""
        fac_key = facility_id.upper()
        if fac_key in FACILITY_REGISTRY:
            meta = FACILITY_REGISTRY[fac_key]
            return {
                "id": meta["id"].lower(),
                "key": meta["id"],
                "name": meta["name"],
                "city": meta["location"],
                "lat": meta["lat"],
                "lon": meta["lon"],
                "it_load_mw": meta["it_load_mw"],
                "baseline_pue": meta["baseline_pue"],
                "electricity_cost_kwh": meta["utility_rate_kwh"],
                "status": "Operational" if meta["id"] != "PHOENIX" else "Thermal Stress Warning",
                "cooling_infrastructure": "Indirect/Direct Economizer + Adiabatic Trim & Backup DX Chillers",
            }
        return self.get_facility_list()[0]

    def get_full_analytics(self, facility_id: str, selected_hour: int = 14, temp_offset: float = 0.0) -> Dict[str, Any]:
        """Run the end-to-end LangGraph pipeline on the selected facility."""
        fac_name = facility_id.lower().replace("-va", "").replace("-az", "").replace("-ca", "")
        if "ashburn" in fac_name:
            fac_name = "ashburn"
        elif "phoenix" in fac_name:
            fac_name = "phoenix"
        elif "sanjose" in fac_name:
            fac_name = "sanjose"
        else:
            fac_name = "ashburn"

        # Load raw data and apply transformations
        meta, df = load_facility_json(fac_name)
        # Normalize key aliases between JSON schema and FACILITY_REGISTRY schema
        if "utility_rate_kwh" not in meta and "electricity_rate_kwh" in meta:
            meta["utility_rate_kwh"] = meta["electricity_rate_kwh"]
        if "location" not in meta:
            meta["location"] = meta.get("name", fac_name)
        
        if temp_offset != 0.0:
            df["apparent_temperature_celsius"] = df["apparent_temperature_celsius"] + temp_offset
            df["wet_bulb_temperature_celsius"] = df["wet_bulb_temperature_celsius"] + (temp_offset * 0.7)

        # Apply cooling decision rules
        df = apply_cooling_rules(df)
        
        # Compute efficiency & financial metrics
        rate = float(meta.get("utility_rate_kwh", meta.get("electricity_rate_kwh", 0.085)))
        it_load = float(meta.get("it_load_mw", 10.0))
        df = compute_energy_metrics(
            df,
            it_load_mw=it_load,
            electricity_rate_kwh=rate
        )
        kpis = generate_kpi_summary(df)

        # Alerts
        alerts = scan_forecast_alerts(df, current_hour=selected_hour)

        # Identify current row
        matching_rows = df[df["hour"] == selected_hour]
        if matching_rows.empty:
            current_row = df.iloc[0].to_dict()
        else:
            current_row = matching_rows.iloc[0].to_dict()

        # Compute workload dispatch recommendation
        dispatch_rec = None
        if current_row["recommended_mode"] == "Mechanical Chiller (DX)":
            for alt_fac in list_available_facilities():
                if alt_fac != fac_name:
                    _, alt_df = load_facility_json(alt_fac)
                    alt_df = apply_cooling_rules(alt_df)
                    alt_row = alt_df[alt_df["hour"] == selected_hour].iloc[0]
                    if alt_row["recommended_mode"] in ["Free-Air Economizer", "Direct Evaporative"]:
                        dispatch_rec = {
                            "target_facility": alt_fac.upper(),
                            "target_mode": alt_row["recommended_mode"],
                            "target_apparent_temp": float(alt_row["apparent_temperature_celsius"]),
                            "recommendation": f"Shift non-urgent batch/AI compute workloads to {alt_fac.upper()} (operating under {alt_row['recommended_mode']} at {alt_row['apparent_temperature_celsius']}°C) to avoid peak DX chiller demand charges."
                        }
                        break

        # Generate narrative text
        narrative_text = (
            f"**Operational Intelligence Summary for {meta['name']}:**\n\n"
            f"At operational hour **{current_row.get('timestamp', f'{selected_hour}:00')}**, the facility is operating under "
            f"**{current_row['recommended_mode']}**. Outdoor apparent temperature is **{current_row['apparent_temperature_celsius']}°C** "
            f"with wet-bulb at **{current_row['wet_bulb_temperature_celsius']}°C** and air quality PM2.5 at **{int(current_row['air_quality_pm2p5_idx'])}**.\n\n"
            f"**Reason:** {current_row['mode_reason']}\n\n"
            f"**24-Hour Fleet Optimization:** Dynamic psychrometric economization enables **{kpis['eco_hours']} / 24 hours** "
            f"of compressor-free operation, delivering **${kpis['total_savings_usd']:,.2f}** in projected daily cost savings "
            f"and avoiding **{kpis['total_co2_tons']:.2f} metric tons** of CO₂ emissions."
        )

        return {
            "facility_meta": meta,
            "selected_hour": selected_hour,
            "processed_df": df,
            "current_metrics": current_row,
            "kpis": kpis,
            "alerts": alerts,
            "dispatch_recommendation": dispatch_rec,
            "narrative": narrative_text,
        }

    def get_multi_facility_comparison(self, temp_offset: float = 0.0) -> pd.DataFrame:
        """Run multi-facility benchmarking table with dynamically computed site metrics."""
        facilities = list_available_facilities()
        rows = []
        
        for fac_id in facilities:
            meta, df = load_facility_json(fac_id)
            if temp_offset != 0.0:
                df["apparent_temperature_celsius"] = df["apparent_temperature_celsius"] + temp_offset
                df["wet_bulb_temperature_celsius"] = df["wet_bulb_temperature_celsius"] + (temp_offset * 0.7)
            
            df = apply_cooling_rules(df)
            rate = float(meta.get("utility_rate_kwh", meta.get("electricity_rate_kwh", 0.085)))
            it_load = float(meta.get("it_load_mw", 10.0))
            df = compute_energy_metrics(df, it_load_mw=it_load, electricity_rate_kwh=rate)
            kpis = generate_kpi_summary(df)
            
            # Find representative/peak metrics for this facility
            peak_temp = float(df["apparent_temperature_celsius"].max())
            avg_rh = float(df["relative_humidity_percent"].mean())
            avg_pm25 = float(df["air_quality_pm2p5_idx"].mean())
            avg_pue = round(float(df["projected_pue"].mean()), 2)
            base_pue = float(meta.get("baseline_pue", 1.55))
            daily_savings = float(kpis["total_savings_usd"])
            co2_tons = float(kpis["total_co2_tons"])
            
            # Dominant cooling mode
            mode_counts = df["recommended_mode"].value_counts()
            dominant_mode = mode_counts.index[0] if not mode_counts.empty else "Free-Air Economizer"
            
            risk_score = int(min(100, max(10, (peak_temp / 45.0) * 100)))
            risk_level = "Critical" if risk_score >= 80 else ("Warning" if risk_score >= 50 else "Safe")

            rows.append({
                "Facility Name": meta["name"],
                "Location": meta.get("location", meta["name"]),
                "IT Load (MW)": it_load,
                "Ambient Temp (°C)": round(peak_temp, 1),
                "RH (%)": round(avg_rh, 1),
                "AQI": int(avg_pm25),
                "Recommended Mode": dominant_mode,
                "Baseline PUE": base_pue,
                "Current PUE": avg_pue,
                "PUE Delta": round(avg_pue - base_pue, 2),
                "Current Savings ($/hr)": round(daily_savings / 24.0, 2),
                "12h Projected Savings ($)": round(daily_savings / 2.0, 2),
                "CO2 Avoided (tons)": round(co2_tons, 2),
                "Risk Score (1-100)": risk_score,
                "Risk Level": risk_level,
            })
            
        return pd.DataFrame(rows)

    def get_spatial_heat_grid(self, facility_id: str) -> List[Dict[str, Any]]:
        """Generate microclimate spatial points around facility."""
        from services.mock_data import generate_microclimate_heat_grid
        fac_key = "ashburn-va"
        if "phoenix" in facility_id.lower():
            fac_key = "phoenix-az"
        elif "sanjose" in facility_id.lower():
            fac_key = "sanjose-ca"
        return generate_microclimate_heat_grid(fac_key)
