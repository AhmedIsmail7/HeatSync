import os
from typing import TypedDict, List, Dict, Any, Optional
import pandas as pd
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from data_pipeline import load_facility_json, list_available_facilities
from cooling_engine import apply_cooling_rules
from efficiency_model import compute_energy_metrics, generate_kpi_summary
from alert_engine import scan_forecast_alerts

# --- 1. State Definition (Added dispatch_recommendation) ---
class HeatSyncState(TypedDict):
    facility_name: str
    selected_hour: int
    facility_meta: Dict[str, Any]
    raw_df: Optional[pd.DataFrame]
    processed_df: Optional[pd.DataFrame]
    current_metrics: Dict[str, Any]
    kpis: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    dispatch_recommendation: Optional[Dict[str, Any]]  # <--- Added here
    narrative: str
    errors: List[str]

# --- 2. Node Functions ---
def node_ingest_data(state: HeatSyncState) -> Dict[str, Any]:
    try:
        use_cache = state.get("use_cache", True)
        if use_cache:
            meta, df = load_facility_json(state["facility_name"])
        else:
            from data_pipeline import fetch_facility_data, FACILITY_REGISTRY
            date_str = state.get("date_str", "2024-07-15")
            time_str = state.get("time_str", "14:00")
            df = fetch_facility_data(state["facility_name"], date_str=date_str, time_str=time_str, use_cache=False)
            meta = FACILITY_REGISTRY[state["facility_name"].upper()]
        return {"facility_meta": meta, "raw_df": df}
    except Exception as e:
        return {"errors": [f"Ingestion error: {str(e)}"]}

def node_run_decision_engine(state: HeatSyncState) -> Dict[str, Any]:
    df = state["raw_df"].copy()
    df = apply_cooling_rules(df)
    return {"raw_df": df}

def node_compute_efficiency(state: HeatSyncState) -> Dict[str, Any]:
    df = state["raw_df"]
    meta = state["facility_meta"]
    selected_hour = state["selected_hour"]
    
    df = compute_energy_metrics(
        df,
        it_load_mw=meta["it_load_mw"],
        electricity_rate_kwh=meta["electricity_rate_kwh"]
    )
    kpis = generate_kpi_summary(df)
    current_row = df[df["hour"] == selected_hour].iloc[0].to_dict()
    
    return {
        "processed_df": df,
        "kpis": kpis,
        "current_metrics": current_row
    }

def node_scan_alerts(state: HeatSyncState) -> Dict[str, Any]:
    df = state["processed_df"]
    alerts = scan_forecast_alerts(df, current_hour=state["selected_hour"])
    return {"alerts": alerts}

def node_compute_workload_dispatch(state: HeatSyncState) -> Dict[str, Any]:
    """Recommends compute job shifting when local site is in expensive DX cooling."""
    curr_mode = state["current_metrics"]["recommended_mode"]
    dispatch_rec = None
    
    if curr_mode == "Mechanical Chiller (DX)":
        available = list_available_facilities()
        for alt_fac in available:
            if alt_fac != state["facility_name"]:
                _, alt_df = load_facility_json(alt_fac)
                alt_df = apply_cooling_rules(alt_df)
                alt_row = alt_df[alt_df["hour"] == state["selected_hour"]].iloc[0]
                
                if alt_row["recommended_mode"] in ["Free-Air Economizer", "Direct Evaporative"]:
                    dispatch_rec = {
                        "target_facility": alt_fac.upper(),
                        "target_mode": alt_row["recommended_mode"],
                        "target_apparent_temp": alt_row["apparent_temperature_celsius"],
                        "recommendation": f"Shift non-urgent batch/AI jobs to {alt_fac.upper()} (operating under {alt_row['recommended_mode']} at {alt_row['apparent_temperature_celsius']}°C) to avoid peak chiller demand charges."
                    }
                    break
                    
    return {"dispatch_recommendation": dispatch_rec}

def node_synthesize_narrative(state: HeatSyncState) -> Dict[str, Any]:
    curr = state["current_metrics"]
    kpis = state["kpis"]
    meta = state["facility_meta"]
    
    google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", "")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are HeatSync AI, an expert thermal copilot for mission-critical data center cooling operations."),
        ("user", """
        Facility: {name}
        Timestamp: {timestamp}
        Atmospheric Parameters:
        - Apparent Temp: {temp}°C | Wet-Bulb: {wet_bulb}°C | PM2.5: {pm25} | CO2: {co2} ppm
        
        Selected Dispatch Mode: {mode}
        Reason: {reason}
        
        24-Hour Optimization:
        - Eco-Cooling Hours: {eco_hours} / 24 hrs
        - Projected Daily Cost Savings: ${daily_savings:,.2f}
        - Total Avoided Emissions: {co2_tons:.2f} metric tons CO2e
        
        Task: Write a concise 3-sentence operational action brief for the facility engineer.
        """)
    ])
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.7-flash",
            google_api_key=google_api_key,
            temperature=0.3,
            max_output_tokens=200
        )
        chain = prompt | llm
        response = chain.invoke({
            "name": meta["name"],
            "timestamp": curr["timestamp"],
            "temp": curr["apparent_temperature_celsius"],
            "wet_bulb": curr["wet_bulb_temperature_celsius"],
            "pm25": curr["air_quality_pm2p5_idx"],
            "co2": curr.get("co2_ppm", "N/A"),
            "mode": curr["recommended_mode"],
            "reason": curr["mode_reason"],
            "eco_hours": kpis["eco_hours"],
            "daily_savings": kpis["total_savings_usd"],
            "co2_tons": kpis["total_co2_tons"]
        })
        narrative_text = response.content.strip()
    except Exception:
        narrative_text = (
            f"{meta['name']} is currently operating under {curr['recommended_mode']} at {curr['timestamp']}. "
            f"Active dispatch is dictated by current thermal conditions ({curr['apparent_temperature_celsius']}°C apparent, {curr['wet_bulb_temperature_celsius']}°C wet-bulb). "
            f"Dynamic mode switching achieves an estimated ${kpis['total_savings_usd']:,.2f} in daily avoided cooling costs."
        )
        
    return {"narrative": narrative_text}

# --- 3. Build & Compile LangGraph Workflow ---
def build_heatsync_graph():
    workflow = StateGraph(HeatSyncState)
    
    workflow.add_node("ingest", node_ingest_data)
    workflow.add_node("decision_engine", node_run_decision_engine)
    workflow.add_node("efficiency_math", node_compute_efficiency)
    workflow.add_node("alert_scanner", node_scan_alerts)
    workflow.add_node("workload_dispatch", node_compute_workload_dispatch)  # <--- Added node
    workflow.add_node("narrative_synthesis", node_synthesize_narrative)
    
    workflow.set_entry_point("ingest")
    workflow.add_edge("ingest", "decision_engine")
    workflow.add_edge("decision_engine", "efficiency_math")
    workflow.add_edge("efficiency_math", "alert_scanner")
    workflow.add_edge("alert_scanner", "workload_dispatch")              # <--- Routed here
    workflow.add_edge("workload_dispatch", "narrative_synthesis")        # <--- Routed here
    workflow.add_edge("narrative_synthesis", END)
    
    return workflow.compile()

heatsync_pipeline_app = build_heatsync_graph()
app = heatsync_pipeline_app