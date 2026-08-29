"""FortyGuard Mock Data Provider.

Supplies high-fidelity mock environmental forecasts, decision engine outputs,
psychrometric metrics, and GPT-4o operational narratives for US Data Center
facilities:
- Ashburn, VA (Hyperscale Hub)
- Phoenix, AZ (Desert Heat Stress)
- San José, CA (Silicon Valley Edge)
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
import pandas as pd
import numpy as np


FACILITIES_METADATA = {
    "ashburn-va": {
        "id": "ashburn-va",
        "name": "Ashburn Hyperscale Hub (DC-01)",
        "city": "Ashburn, Virginia",
        "state": "VA",
        "country": "USA",
        "lat": 39.0438,
        "lon": -77.4874,
        "elevation_m": 88,
        "it_load_mw": 45.0,
        "baseline_pue": 1.38,
        "target_pue": 1.15,
        "cooling_infrastructure": "Indirect Evaporative + Free-Air Economizer with Backup DX Chillers",
        "electricity_cost_kwh": 0.085,  # $0.085/kWh (VA industrial rate)
        "grid_carbon_intensity_kg_mwh": 340.0,
        "status": "Operational",
        "status_color": "#10B981",
        "current_active_mode": "Free-Air Cooling",
    },
    "phoenix-az": {
        "id": "phoenix-az",
        "name": "Phoenix Desert Oasis (DC-02)",
        "city": "Phoenix, Arizona",
        "state": "AZ",
        "country": "USA",
        "lat": 33.4484,
        "lon": -112.0740,
        "elevation_m": 331,
        "it_load_mw": 60.0,
        "baseline_pue": 1.48,
        "target_pue": 1.22,
        "cooling_infrastructure": "Hybrid Evaporative Cooling Towers + High-Efficiency Magnetic Bearing Chillers",
        "electricity_cost_kwh": 0.115,  # $0.115/kWh (AZ peak summer rate)
        "grid_carbon_intensity_kg_mwh": 390.0,
        "status": "High Stress Warning",
        "status_color": "#F59E0B",
        "current_active_mode": "Evaporative Cooling",
    },
    "sanjose-ca": {
        "id": "sanjose-ca",
        "name": "San José Innovation DC (DC-03)",
        "city": "San José, California",
        "state": "CA",
        "country": "USA",
        "lat": 37.3382,
        "lon": -121.8863,
        "elevation_m": 25,
        "it_load_mw": 28.0,
        "baseline_pue": 1.32,
        "target_pue": 1.12,
        "cooling_infrastructure": "Direct Air Economizer with Adiabatic Misting and DX Trim",
        "electricity_cost_kwh": 0.165,  # $0.165/kWh (CA industrial peak rate)
        "grid_carbon_intensity_kg_mwh": 210.0,
        "status": "Optimal",
        "status_color": "#10B981",
        "current_active_mode": "Free-Air Cooling",
    },
}


def generate_12h_forecast(facility_id: str, temp_offset: float = 0.0) -> pd.DataFrame:
    """Generate 12-hour hourly forecast DataFrame with environmental metrics,
    cooling recommendations, PUE impact, and financial/carbon savings.
    """
    base_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    hours = [base_time + timedelta(hours=i) for i in range(12)]
    
    meta = FACILITIES_METADATA.get(facility_id, FACILITIES_METADATA["ashburn-va"])
    it_load_kw = meta["it_load_mw"] * 1000.0
    cost_per_kwh = meta["electricity_cost_kwh"]
    carbon_intensity = meta["grid_carbon_intensity_kg_mwh"] / 1000.0  # kg CO2 / kWh
    
    data = []
    
    if facility_id == "ashburn-va":
        # Mild diurnal cycle: 19.5°C in morning -> 25.5°C peak -> 21.0°C evening
        base_temps = [19.5, 20.8, 22.4, 24.1, 25.6, 26.2, 25.8, 24.5, 23.0, 21.5, 20.2, 19.4]
        base_rh = [62.0, 58.0, 52.0, 47.0, 43.0, 42.0, 45.0, 49.0, 55.0, 60.0, 64.0, 68.0]
        base_aqi = [28, 30, 34, 38, 42, 45, 41, 36, 32, 29, 27, 26]
        base_solar = [120, 310, 550, 780, 890, 920, 840, 620, 380, 150, 20, 0]
    elif facility_id == "phoenix-az":
        # Extreme desert heat: 32.0°C in morning -> 41.5°C peak -> 36.0°C evening
        base_temps = [32.0, 34.2, 36.8, 38.9, 40.8, 41.8, 41.2, 39.7, 38.1, 36.5, 35.0, 33.8]
        base_rh = [24.0, 21.0, 18.0, 15.0, 13.0, 12.0, 14.0, 16.0, 19.0, 22.0, 23.0, 25.0]
        base_aqi = [45, 52, 58, 64, 72, 78, 75, 68, 60, 54, 49, 46]
        base_solar = [220, 480, 720, 910, 1020, 1060, 980, 810, 530, 260, 40, 0]
    else:  # sanjose-ca
        # Coastal temperate: 17.0°C -> 23.5°C peak -> 18.2°C evening
        base_temps = [17.0, 18.2, 19.8, 21.5, 23.2, 23.8, 23.0, 21.8, 20.1, 18.9, 17.8, 17.2]
        base_rh = [68.0, 62.0, 56.0, 50.0, 46.0, 44.0, 48.0, 54.0, 61.0, 67.0, 71.0, 74.0]
        base_aqi = [32, 35, 38, 40, 44, 46, 42, 39, 36, 33, 31, 30]
        base_solar = [150, 360, 610, 820, 930, 960, 880, 670, 410, 180, 25, 0]

    for i in range(12):
        t = round(base_temps[i] + temp_offset, 1)
        rh = base_rh[i]
        aqi = base_aqi[i]
        solar = base_solar[i]
        hour_dt = hours[i]
        
        # Psychrometric decision rules
        # Mode Classification logic:
        # If Dry Bulb <= 22°C and AQI <= 50 -> Free-Air Cooling
        # If Dry Bulb 22.1°C to 28°C and RH <= 65% and AQI <= 70 -> Evaporative Cooling
        # If Dry Bulb > 28°C or AQI > 70 or (Dry Bulb > 26 and RH > 65%) -> Mechanical DX Cooling
        if t <= 22.0 and aqi <= 50:
            rec_mode = "Free-Air Cooling"
            pue_val = 1.12
            pue_delta = round(pue_val - meta["baseline_pue"], 3)  # e.g., 1.12 - 1.38 = -0.26
            cooling_power_kw = it_load_kw * (pue_val - 1.0)
            baseline_cooling_kw = it_load_kw * (meta["baseline_pue"] - 1.0)
            saved_kw = max(0.0, baseline_cooling_kw - cooling_power_kw)
            risk_level = "Safe"
            risk_score = 15
        elif t <= 28.0 and aqi <= 70 and rh <= 65.0:
            rec_mode = "Evaporative Cooling"
            pue_val = 1.20
            pue_delta = round(pue_val - meta["baseline_pue"], 3)  # e.g., 1.20 - 1.38 = -0.18
            cooling_power_kw = it_load_kw * (pue_val - 1.0)
            baseline_cooling_kw = it_load_kw * (meta["baseline_pue"] - 1.0)
            saved_kw = max(0.0, baseline_cooling_kw - cooling_power_kw)
            risk_level = "Moderate"
            risk_score = 42
        else:
            rec_mode = "Mechanical DX Cooling"
            pue_val = round(meta["baseline_pue"] + ((t - 28.0) * 0.008), 2)
            pue_delta = round(pue_val - meta["baseline_pue"], 3)
            cooling_power_kw = it_load_kw * (pue_val - 1.0)
            baseline_cooling_kw = it_load_kw * (meta["baseline_pue"] - 1.0)
            saved_kw = 0.0  # Running full DX, minimum savings
            risk_level = "High Risk" if t >= 36.0 else "Warning"
            risk_score = min(98, int(55 + (t - 28.0) * 3.5))

        hourly_cost_savings = round(saved_kw * cost_per_kwh, 2)
        hourly_co2_savings = round(saved_kw * carbon_intensity, 2)
        
        data.append({
            "timestamp": hour_dt,
            "time_str": hour_dt.strftime("%H:%M"),
            "hour_label": hour_dt.strftime("%I:%M %p"),
            "dry_bulb_temp_c": t,
            "relative_humidity_pct": rh,
            "aqi": aqi,
            "solar_irradiance_wm2": solar,
            "recommended_mode": rec_mode,
            "pue": pue_val,
            "pue_delta": pue_delta,
            "saved_power_kw": round(saved_kw, 1),
            "hourly_cost_savings_usd": hourly_cost_savings,
            "hourly_co2_savings_kg": hourly_co2_savings,
            "risk_level": risk_level,
            "risk_score": risk_score,
        })
        
    df = pd.DataFrame(data)
    
    # Identify mode switch points
    df["prev_mode"] = df["recommended_mode"].shift(1)
    df["is_switch_point"] = (df["recommended_mode"] != df["prev_mode"]) & (df["prev_mode"].notna())
    
    switch_notes = []
    for idx, row in df.iterrows():
        if row["is_switch_point"]:
            switch_notes.append(f"Switch: {row['prev_mode']} ➔ {row['recommended_mode']}")
        else:
            switch_notes.append("")
    df["switch_note"] = switch_notes
    
    return df


def get_ai_narrative(facility_id: str, current_temp: float, current_mode: str, df_forecast: pd.DataFrame) -> Dict[str, Any]:
    """Provide structured GPT-4o / Decision Engine operational narrative and alerts."""
    meta = FACILITIES_METADATA.get(facility_id, FACILITIES_METADATA["ashburn-va"])
    
    # Find mode switches in next 12h
    switches = df_forecast[df_forecast["is_switch_point"]]
    
    if facility_id == "ashburn-va":
        narrative = (
            f"**Operational Intelligence Summary for {meta['name']}:**\n\n"
            f"Current outdoor dry-bulb temperature is **{current_temp}°C** with relative humidity at **58%**. "
            f"Conditions are within the **ASHRAE A1 Recommended Envelope**, enabling full **{current_mode}** "
            f"operation with **-0.26 PUE reduction** relative to baseline DX chillers.\n\n"
            f"**Key Anticipated Transition:** As solar irradiance ramps towards peak afternoon values (~890 W/m²), "
            f"ambient temperatures will cross the **22.0°C economizer threshold** around 12:00 PM. The system "
            f"recommends staging **Indirect Evaporative Cooling** between 12:00 PM and 17:00 PM before transitioning "
            f"back to 100% Free-Air cooling in the late evening."
        )
        alerts = [
            {
                "id": "ALT-ASH-01",
                "severity": "info",
                "title": "Optimal Free-Air Economizer Window Active",
                "message": f"Ambient dry-bulb ({current_temp}°C) and AQI (30) allow 100% economizer airflow. Chiller compressors remain staged off.",
                "action": "Maintain economizer damper modulation at 85-100%. Monitor filter differential pressure.",
                "timestamp": "Live Active",
            },
            {
                "id": "ALT-ASH-02",
                "severity": "warning",
                "title": "Approaching Afternoon Evaporative Staging Threshold",
                "message": "Ambient temperature projected to exceed 24°C at 13:00 PM. Evaporative wet-pads pre-wetting required.",
                "action": "Verify adiabatic water supply pressure and initiate water sump pump circulation test at 11:30 AM.",
                "timestamp": "Forecast +3.5h",
            },
        ]
        heat_risk = "Safe (Low Risk)"
        risk_color = "#10B981"
        confidence_score = 96.4

    elif facility_id == "phoenix-az":
        narrative = (
            f"**Operational Intelligence Summary for {meta['name']}:**\n\n"
            f"**Critical Heat Advisory:** Ambient dry-bulb temperature is currently **{current_temp}°C** with low relative humidity (21%). "
            f"High thermal stress is projected across the entire Phoenix basin, with temperatures peaking at **41.8°C** at 15:00 PM.\n\n"
            f"**Immediate Action Protocol:** While evaporative cooling is currently active, high ambient wet-bulb and solar irradiance "
            f"exceed adiabatic heat rejection capacity. The system projects a mandatory shift to **Mechanical DX Cooling** at 11:00 AM. "
            f"Facility operators must pre-cool chilled water loops and verify chiller redundancy (N+2 readiness) to prevent thermal excursions on high-density server racks."
        )
        alerts = [
            {
                "id": "ALT-PHX-01",
                "severity": "critical",
                "title": "Severe Heat Stress Spike – Chiller Transition Mandatory",
                "message": "Ambient dry-bulb expected to breach 40°C threshold. Evaporative cooling cannot maintain ASHRAE A1 inlet temperatures.",
                "action": "Engage primary centrifugal chillers CH-01 through CH-04. Verify condenser fan speeds at 100%.",
                "timestamp": "Imminent (+1.5h)",
            },
            {
                "id": "ALT-PHX-02",
                "severity": "warning",
                "title": "Grid Peak Demand Pricing Event",
                "message": "Arizona utility peak tariff active ($0.115/kWh). Mechanical DX load will increase facility hourly power consumption by 18.5%.",
                "action": "Cap non-essential facility loads. Enable UPS eco-mode where validated.",
                "timestamp": "13:00 - 18:00 MST",
            },
            {
                "id": "ALT-PHX-03",
                "severity": "info",
                "title": "Particulate Matter / AQI Elevated",
                "message": "AQI level at 72 (Moderate particulate index). Dust mitigation filters in place.",
                "action": "Inspect pre-filters on AHU-10 to AHU-24.",
                "timestamp": "Live Active",
            },
        ]
        heat_risk = "High Risk (Thermal Stress)"
        risk_color = "#EF4444"
        confidence_score = 98.1

    else:  # sanjose-ca
        narrative = (
            f"**Operational Intelligence Summary for {meta['name']}:**\n\n"
            f"Optimal coastal microclimate conditions observed. Ambient dry-bulb is **{current_temp}°C** with relative humidity at **62%**. "
            f"Air quality index is pristine (**AQI 35**). Direct economizer airside free cooling is operating with maximum thermodynamic efficiency.\n\n"
            f"**Forecast Stability:** No severe heat spikes detected over the 12-hour horizon. Minor afternoon peak of 23.8°C will require "
            f"light adiabatic trim misting between 13:00 and 16:00, generating an estimated cumulative savings of **$4,120** over the next 12 hours."
        )
        alerts = [
            {
                "id": "ALT-SJC-01",
                "severity": "info",
                "title": "Maximum Free Cooling Efficiency Active",
                "message": "Facility operating at PUE 1.12 (-0.20 delta vs baseline). Compressor energy consumption reduced by 88%.",
                "action": "Maintain automated economizer modulation profile.",
                "timestamp": "Live Active",
            },
            {
                "id": "ALT-SJC-02",
                "severity": "info",
                "title": "Afternoon Adiabatic Trim Pulse Scheduled",
                "message": "Low-volume misting pulse scheduled for 13:30 to 15:30 to counteract solar gain on roof AHU units.",
                "action": "Ensure RO water tank level is above 75%.",
                "timestamp": "Forecast +3h",
            },
        ]
        heat_risk = "Safe (Optimal)"
        risk_color = "#10B981"
        confidence_score = 95.8

    return {
        "facility_id": facility_id,
        "facility_name": meta["name"],
        "heat_risk": heat_risk,
        "risk_color": risk_color,
        "confidence_score": confidence_score,
        "llm_model": "GPT-4o Reasoning (Orchestrated via LangGraph)",
        "summary_narrative": narrative,
        "alerts": alerts,
        "switch_points_count": len(switches),
        "total_estimated_12h_cost_savings": round(df_forecast["hourly_cost_savings_usd"].sum(), 2),
        "total_estimated_12h_co2_savings": round(df_forecast["hourly_co2_savings_kg"].sum(), 1),
    }


def generate_microclimate_heat_grid(facility_id: str, radius_km: float = 3.5, grid_size: int = 15) -> List[Dict[str, Any]]:
    """Generate spatial heat points for PyDeck / 3D thermal layer around the data center facility."""
    meta = FACILITIES_METADATA.get(facility_id, FACILITIES_METADATA["ashburn-va"])
    center_lat = meta["lat"]
    center_lon = meta["lon"]
    
    # Scale base temp according to facility
    if facility_id == "ashburn-va":
        base_t = 23.5
    elif facility_id == "phoenix-az":
        base_t = 39.0
    else:
        base_t = 21.0
        
    points = []
    # Generate a grid around the facility
    lat_step = (radius_km / 111.0) / (grid_size / 2.0)
    lon_step = (radius_km / (111.0 * np.cos(np.radians(center_lat)))) / (grid_size / 2.0)
    
    for i in range(-grid_size // 2, grid_size // 2 + 1):
        for j in range(-grid_size // 2, grid_size // 2 + 1):
            p_lat = center_lat + (i * lat_step)
            p_lon = center_lon + (j * lon_step)
            dist = np.sqrt(i**2 + j**2)
            
            # Urban Heat Island (UHI) simulation with asphalt & roof effect near DC
            heat_delta = np.sin(i * 0.4) * np.cos(j * 0.4) * 2.2 + (2.5 if dist < 2.0 else -0.5 * dist / 5.0)
            point_temp = round(base_t + heat_delta, 1)
            
            # Color coding based on temp
            if point_temp < 22.0:
                color = [13, 148, 136, 160]  # Teal / Free-Air
            elif point_temp < 28.0:
                color = [2, 132, 199, 170]   # Sky blue / Evaporative
            elif point_temp < 36.0:
                color = [245, 158, 11, 180]  # Amber / High temp
            else:
                color = [239, 68, 68, 200]   # Red / Extreme heat
                
            points.append({
                "latitude": p_lat,
                "longitude": p_lon,
                "temperature_c": point_temp,
                "elevation": max(10.0, float((point_temp - 15.0) * 25.0)),
                "color": color,
                "heat_intensity": min(1.0, max(0.1, (point_temp - 15.0) / 30.0))
            })
            
    return points
