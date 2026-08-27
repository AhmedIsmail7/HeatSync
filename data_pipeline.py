import os
import json
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def list_available_facilities() -> list:
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    return [f.replace("_env.json", "") for f in os.listdir(DATA_DIR) if f.endswith("_env.json")]

def load_facility_json(facility_name: str = "ashburn") -> tuple[dict, pd.DataFrame]:
    filepath = os.path.join(DATA_DIR, f"{facility_name}_env.json")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Missing dataset: {filepath}")

    with open(filepath, "r") as f:
        payload = json.load(f)
        
    meta = payload["location"]
    df = pd.DataFrame(payload["hourly_records"])
    
    # Extract integer hour from "00:00" -> 0
    df["hour"] = df["timestamp"].apply(lambda t: int(t.split(":")[0]))
    
    return meta, df