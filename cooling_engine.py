import pandas as pd
from typing import Tuple

def classify_cooling_mode(row: pd.Series) -> Tuple[str, str]:
    """
    ASHRAE Thermal Comfort & Data Center Economizer Guidelines:
    - Free-Air Economizer: Apparent Temp <= 19.0°C, RH < 85%, PM2.5 < 55
    - Direct Evaporative: Wet-bulb <= 18.5°C, Apparent Temp <= 27.0°C, PM2.5 < 60
    - Mechanical DX Chiller: Default when ambient thermal stress or particulate counts exceed safe limits
    """
    apparent_temp = float(row["apparent_temperature_celsius"])
    wet_bulb = float(row["wet_bulb_temperature_celsius"])
    pm25 = float(row["air_quality_pm2p5_idx"])
    rh = float(row["relative_humidity_percent"])
    co2 = float(row.get("co2_ppm", 400.0))

    # 1. Free-Air Direct Economizer
    if apparent_temp <= 19.0 and rh < 85.0 and pm25 < 55.0:
        return (
            "Free-Air Economizer",
            "Low ambient apparent temperature and safe particulate levels allow direct outdoor air intake."
        )

    # 2. Direct Evaporative (Adiabatic Cooling)
    elif wet_bulb <= 18.5 and apparent_temp <= 27.0 and pm25 < 60.0:
        return (
            "Direct Evaporative",
            f"Favorable wet-bulb depression ({apparent_temp - wet_bulb:.1f}°C delta) enables adiabatic cooling."
        )

    # 3. Mechanical DX Refrigeration
    else:
        triggers = []
        if apparent_temp > 27.0:
            triggers.append(f"Apparent Temp ({apparent_temp:.1f}°C) > 27°C")
        if wet_bulb > 18.5:
            triggers.append(f"Wet-Bulb ({wet_bulb:.1f}°C) > 18.5°C")
        if pm25 >= 55.0:
            triggers.append(f"PM2.5 index ({int(pm25)}) exceeds safe intake threshold")
            
        reason = "Active DX compressor required: " + ", ".join(triggers) + "."
        return ("Mechanical Chiller (DX)", reason)

def apply_cooling_rules(df: pd.DataFrame) -> pd.DataFrame:
    results = df.apply(classify_cooling_mode, axis=1, result_type="expand")
    df["recommended_mode"] = results[0]
    df["mode_reason"] = results[1]
    return df