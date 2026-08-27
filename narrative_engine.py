import os
from openai import OpenAI

def get_llm_client() -> OpenAI:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY", "dummy_token")
    return OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=token
    )

def generate_risk_narrative(current_row: dict, kpis: dict, facility_meta: dict) -> str:
    prompt = f"""
    You are HeatSync AI, an expert thermal intelligence copilot for data center operations.
    
    Facility: {facility_meta['name']}
    Timestamp: {current_row['timestamp']}
    Atmospheric Parameters:
    - Apparent Temperature: {current_row['apparent_temperature_celsius']}°C
    - Wet-Bulb Temperature: {current_row['wet_bulb_temperature_celsius']}°C
    - Relative Humidity: {current_row['relative_humidity_percent']}%
    - PM2.5 Index: {current_row['air_quality_pm2p5_idx']}
    - CO2: {current_row.get('co2_ppm', 'N/A')} ppm
    
    Active Dispatch Mode: {current_row['recommended_mode']}
    Mode Reason: {current_row['mode_reason']}
    
    24-Hour Optimization KPIs:
    - Free-Air / Evaporative Hours: {kpis['eco_hours']} / 24 hrs
    - Estimated Daily Savings: ${kpis['total_savings_usd']:,.2f}
    - Avoided Emissions: {kpis['total_co2_tons']:.2f} metric tons CO2e
    
    Task: Write a concise 3-sentence operational action brief:
    1. State current dispatch mode and primary atmospheric trigger.
    2. Note forecasted cooling mode shifts.
    3. Quantify the financial and energy efficiency benefit.
    """
    
    try:
        client = get_llm_client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return (
            f"{facility_meta['name']} is currently operating under {current_row['recommended_mode']} at {current_row['timestamp']}. "
            f"Active dispatch is dictated by current thermal conditions ({current_row['apparent_temperature_celsius']}°C apparent, {current_row['wet_bulb_temperature_celsius']}°C wet-bulb). "
            f"Over the full 24-hour cycle, dynamic mode switching delivers an estimated ${kpis['total_savings_usd']:,.2f} in avoided cooling costs."
        )