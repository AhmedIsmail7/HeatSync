import pandas as pd

def scan_forecast_alerts(df: pd.DataFrame, current_hour: int = 14) -> list[dict]:
    """
    Scans the next 12 hours from current_hour for thermal risk thresholds
    and cooling mode transition penalties.
    """
    alerts = []
    horizon_df = df[(df["hour"] > current_hour) & (df["hour"] <= current_hour + 12)].copy()
    
    if horizon_df.empty:
        return alerts

    for _, row in horizon_df.iterrows():
        h = int(row["hour"])
        time_str = row["timestamp"]
        mode = row["recommended_mode"]
        temp = row["apparent_temperature_celsius"]
        pm25 = row["air_quality_pm2p5_idx"]

        # Alert: Heat spikes forcing DX cooling
        if mode == "Mechanical Chiller (DX)" and temp >= 28.0:
            alerts.append({
                "hour": h,
                "timestamp": time_str,
                "severity": "CRITICAL",
                "title": f"Chiller Peak Load Risk at {time_str}",
                "message": f"Apparent temperature reaches {temp:.1f}°C. Expect full DX compressor activation."
            })

        # Alert: Air Quality excursions restricting economization
        if pm25 >= 58.0:
            alerts.append({
                "hour": h,
                "timestamp": time_str,
                "severity": "WARNING",
                "title": f"Air Quality Cutoff at {time_str}",
                "message": f"PM2.5 index reaches {int(pm25)}. Free-air economizer blocked to protect server intake filters."
            })
            
    return alerts