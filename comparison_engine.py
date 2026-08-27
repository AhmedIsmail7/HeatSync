import pandas as pd
from data_pipeline import list_available_facilities, load_facility_json
from cooling_engine import apply_cooling_rules
from efficiency_model import compute_energy_metrics, generate_kpi_summary

def compare_all_facilities() -> pd.DataFrame:
    """Runs all available facilities and returns a comparative benchmarking table."""
    facilities = list_available_facilities()
    rows = []
    
    for fac_id in facilities:
        meta, df = load_facility_json(fac_id)
        df = apply_cooling_rules(df)
        df = compute_energy_metrics(
            df, 
            it_load_mw=meta["it_load_mw"], 
            electricity_rate_kwh=meta["electricity_rate_kwh"]
        )
        kpis = generate_kpi_summary(df)
        
        rows.append({
            "Facility": meta["name"],
            "IT Load": f"{meta['it_load_mw']} MW",
            "Peak Temp (°C)": df["apparent_temperature_celsius"].max(),
            "Eco-Cooling Hours": f"{kpis['eco_hours']} / 24 hrs",
            "Avg PUE": round(df["projected_pue"].mean(), 2),
            "Daily Savings ($)": round(kpis["total_savings_usd"], 2),
            "CO2 Avoided (tons)": round(kpis["total_co2_tons"], 2)
        })
        
    return pd.DataFrame(rows)