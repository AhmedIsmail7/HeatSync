import pandas as pd

# PUE Lookups per operational mode
PUE_LOOKUP = {
    "Free-Air Economizer": 1.10,
    "Direct Evaporative": 1.25,
    "Mechanical Chiller (DX)": 1.55
}
BASELINE_PUE = 1.55
US_GRID_CO2_PER_KWH = 0.385  # kg CO2 / kWh

def compute_energy_metrics(
    df: pd.DataFrame, 
    it_load_mw: float = 10.0, 
    electricity_rate_kwh: float = 0.085
) -> pd.DataFrame:
    """
    Computes facility power consumption, efficiency shifts, and financial metrics.
    """
    df["projected_pue"] = df["recommended_mode"].map(PUE_LOOKUP)
    df["pue_delta_pct"] = ((df["projected_pue"] - BASELINE_PUE) / BASELINE_PUE) * 100.0

    # Total Facility Power (kW) = IT Load (kW) * PUE
    it_load_kw = it_load_mw * 1000.0
    df["baseline_facility_kw"] = it_load_kw * BASELINE_PUE
    df["optimized_facility_kw"] = it_load_kw * df["projected_pue"]
    
    # Savings compared to always-mechanical DX baseline
    df["hourly_kwh_saved"] = df["baseline_facility_kw"] - df["optimized_facility_kw"]
    df["hourly_cost_saved_usd"] = df["hourly_kwh_saved"] * electricity_rate_kwh
    df["hourly_co2_avoided_kg"] = df["hourly_kwh_saved"] * US_GRID_CO2_PER_KWH

    return df

def generate_kpi_summary(df: pd.DataFrame) -> dict:
    """Calculates high-level aggregated metrics for the summary cards."""
    eco_hours = int((df["recommended_mode"] != "Mechanical Chiller (DX)").sum())
    total_savings_usd = float(df["hourly_cost_saved_usd"].sum())
    total_co2_tons = float(df["hourly_co2_avoided_kg"].sum() / 1000.0)
    avg_pue_reduction = float(df["pue_delta_pct"].mean())

    return {
        "eco_hours": eco_hours,
        "total_savings_usd": total_savings_usd,
        "total_co2_tons": total_co2_tons,
        "avg_pue_reduction_pct": avg_pue_reduction
    }