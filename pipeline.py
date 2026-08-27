import pandas as pd
from orchestration_graph import heatsync_pipeline_app
from data_pipeline import list_available_facilities
from comparison_engine import compare_all_facilities

def get_heat_sync_analytics(facility_name: str = "ashburn", selected_hour: int = 14) -> dict:
    initial_state = {
        "facility_name": facility_name,
        "selected_hour": selected_hour,
        "facility_meta": {},
        "raw_df": None,
        "processed_df": None,
        "current_metrics": {},
        "kpis": {},
        "alerts": [],
        "dispatch_recommendation": None,  # <--- Initialized here
        "narrative": "",
        "errors": []
    }
    
    final_state = heatsync_pipeline_app.invoke(initial_state)
    
    return {
        "facility_meta": final_state["facility_meta"],
        "selected_hour": selected_hour,
        "current_metrics": final_state["current_metrics"],
        "hourly_timeseries": final_state["processed_df"].to_dict(orient="records"),
        "kpis": final_state["kpis"],
        "alerts": final_state["alerts"],
        "dispatch_recommendation": final_state["dispatch_recommendation"],  # <--- Returned here
        "narrative": final_state["narrative"]
    }

if __name__ == "__main__":
    print("Testing Updated LangGraph Pipeline (6 Nodes)...")
    res = get_heat_sync_analytics("ashburn", selected_hour=14)
    print("Current Mode:", res["current_metrics"]["recommended_mode"])
    print("Dispatch Rec:", res["dispatch_recommendation"])
    print("\nBenchmark Table:")
    print(compare_all_facilities())