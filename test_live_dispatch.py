from datetime import datetime, timezone
import json
from data_pipeline import fetch_facility_data, FACILITY_REGISTRY
from cooling_engine import apply_cooling_rules
from orchestration_graph import app as graph_app
from dotenv import load_dotenv

load_dotenv()

def run_live_test():
    now_utc = datetime.now(timezone.utc)
    current_date = now_utc.strftime("%Y-%m-%d")
    current_time = now_utc.strftime("%H:00")
    selected_hour = now_utc.hour
    
    print("=" * 60)
    print(f"HEATSYNC REAL-TIME LIVE INGESTION TEST")
    print(f"Timestamp: {current_date} {current_time} UTC")
    print("=" * 60)

    # 2. Test live fetch across the facilities
    for facility_key in ["ASHBURN", "PHOENIX", "SANJOSE"]:
        print(f"\n[+] Fetching live microclimate telemetry for {facility_key}...")
        try:
            # Force live API call by passing use_cache=False
            df = fetch_facility_data(
                facility_id=facility_key,
                date_str=current_date,
                time_str=current_time,
                use_cache=False
            )
            
            # Extract current hour readings
            row = df[df["hour"] == selected_hour].iloc[0]
            
            t_app = row.get("apparent_temperature_celsius", row.get("T_apparent"))
            t_wb = row.get("wet_bulb_temperature_celsius", row.get("T_wb"))
            rh = row.get("relative_humidity_percent", row.get("RH"))
            pm25 = row.get("air_quality_pm2p5_idx", row.get("pm25"))
            
            print(f"    - Live T_apparent: {t_app:.1f}°C")
            print(f"    - Live T_wetbulb:  {t_wb:.1f}°C")
            print(f"    - Live Humidity:   {rh:.1f}%")
            print(f"    - Live PM2.5:      {pm25:.1f}")
            
        except Exception as e:
            print(f"    [-] Failed to fetch live data for {facility_key}: {e}")

    # 3. Run full LangGraph State Engine for Ashburn with live input
    print("\n" + "=" * 60)
    print("RUNNING FULL LIVE LANGGRAPH WORKFLOW (Ashburn DC-1)")
    print("=" * 60)
    
    initial_state = {
        "facility_name": "ASHBURN",
        "selected_hour": selected_hour,
        "facility_meta": FACILITY_REGISTRY["ASHBURN"],
        "date_str": current_date,
        "time_str": current_time,
        "use_cache": False,
        "errors": []
    }
    
    final_output = graph_app.invoke(initial_state)
    
    curr_m = final_output.get('current_metrics', {})
    print(f"\nRecommended Cooling Mode: {curr_m.get('recommended_mode', 'N/A')}")
    print(f"Projected PUE:            {curr_m.get('projected_pue', 'N/A')}")
    print(f"Cross-Facility Dispatch:  {final_output.get('dispatch_recommendation')}")
    print("\n--- LLM Operational Narrative (Gemini 3.7 Flash) ---")
    print(final_output.get("narrative", "No narrative generated."))

if __name__ == "__main__":
    run_live_test()
