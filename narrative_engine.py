import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

def generate_risk_narrative(current_row: dict, kpis: dict, facility_meta: dict) -> str:
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
        
        Task: Write a concise 3-sentence operational action brief for the facility engineer:
        1. State current dispatch mode and primary atmospheric trigger.
        2. Note forecasted cooling mode shifts.
        3. Quantify the financial and energy efficiency benefit.
        """)
    ])

    # Try Gemini models in order of capability & availability
    models_to_try = ["gemini-3.7-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    
    for model_name in models_to_try:
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=google_api_key,
                temperature=0.3,
                max_output_tokens=1024,
            )
            chain = prompt | llm
            response = chain.invoke({
                "name": facility_meta["name"],
                "timestamp": current_row["timestamp"],
                "temp": current_row["apparent_temperature_celsius"],
                "wet_bulb": current_row["wet_bulb_temperature_celsius"],
                "pm25": current_row["air_quality_pm2p5_idx"],
                "co2": current_row.get("co2_ppm", "N/A"),
                "mode": current_row["recommended_mode"],
                "reason": current_row["mode_reason"],
                "eco_hours": kpis["eco_hours"],
                "daily_savings": kpis["total_savings_usd"],
                "co2_tons": kpis["total_co2_tons"],
            })
            if response and response.content:
                return str(response.content).strip()
        except Exception:
            continue

    # Clean fallback if all remote calls fail or no key is present
    return (
        f"{facility_meta['name']} is currently operating under {current_row['recommended_mode']} at {current_row['timestamp']}. "
        f"Active dispatch is dictated by current thermal conditions ({current_row['apparent_temperature_celsius']}°C apparent, {current_row['wet_bulb_temperature_celsius']}°C wet-bulb). "
        f"Over the full 24-hour cycle, dynamic mode switching delivers an estimated ${kpis['total_savings_usd']:,.2f} in avoided cooling costs."
    )