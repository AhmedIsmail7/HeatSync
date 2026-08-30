"""FortyGuard / HeatSync Top KPI Cards Component.

Renders real-time metric cards for Ambient Apparent Temp, Recommended Cooling Mode,
PUE Delta, Hourly Cost Savings, and secondary atmospheric indicators.
"""

from typing import Any, Dict
import streamlit as st
from utils.helpers import c_to_f, format_currency, format_co2, get_mode_badge_html


def render_kpi_cards(
    current_metrics: Dict[str, Any],
    kpis: Dict[str, Any],
    facility_meta: Dict[str, Any],
    unit_pref: str = "Celsius (°C)",
    dispatch_rec: Dict[str, Any] = None,
) -> None:
    """Render top operational KPI cards and secondary environmental indicators."""
    is_f = "Fahrenheit" in unit_pref
    temp_unit = "°F" if is_f else "°C"
    
    app_temp_c = float(current_metrics.get("apparent_temperature_celsius", 22.0))
    wet_bulb_c = float(current_metrics.get("wet_bulb_temperature_celsius", 16.5))
    pm25 = float(current_metrics.get("air_quality_pm2p5_idx", 35.0))
    rh = float(current_metrics.get("relative_humidity_percent", 50.0))
    co2_ppm = float(current_metrics.get("co2_ppm", 400.0))
    
    display_temp = c_to_f(app_temp_c) if is_f else app_temp_c
    display_wb = c_to_f(wet_bulb_c) if is_f else wet_bulb_c
    
    rec_mode = current_metrics.get("recommended_mode", "Free-Air Economizer")
    
    projected_pue = float(current_metrics.get("projected_pue", 1.25))
    baseline_pue = float(facility_meta.get("baseline_pue", 1.55))
    pue_delta_pct = float(current_metrics.get("pue_delta_pct", -19.3))
    
    hourly_savings = float(current_metrics.get("hourly_cost_saved_usd", 0.0))
    hourly_kwh_saved = float(current_metrics.get("hourly_kwh_saved", 0.0))

    # Workload Dispatch Banner (if active)
    if dispatch_rec:
        st.markdown(
            f"""
            <div style="background: #F0F9FF; border: 1px solid #BAE6FD; border-left: 4px solid #0284C7; border-radius: 8px; padding: 0.85rem 1.15rem; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 3px;">
                    <span style="font-size: 0.8rem; font-weight: 700; color: #0369A1; text-transform: uppercase; letter-spacing: 0.04em;">
                        Workload Dispatch Optimization
                    </span>
                    <span style="background: #0284C7; color: white; padding: 2px 8px; border-radius: 9999px; font-size: 0.7rem; font-weight: 700;">
                        Target: {dispatch_rec['target_facility']}
                    </span>
                </div>
                <div style="font-size: 0.82rem; color: #334155; line-height: 1.4;">
                    {dispatch_rec['recommendation']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 4 Primary KPI Columns
    col1, col2, col3, col4 = st.columns(4)

    # Card 1: Ambient Apparent Temperature
    with col1:
        st.markdown(
            f"""
            <div class="kpi-card highlight">
                <div>
                    <div class="kpi-title">
                        <span>Apparent Temperature</span>
                        <span style="font-size: 0.68rem; color: #0284C7; font-weight: 700;">FORTYGUARD</span>
                    </div>
                    <div class="kpi-value">
                        {display_temp:.1f}<span class="kpi-unit">{temp_unit}</span>
                    </div>
                </div>
                <div class="kpi-delta delta-neutral">
                    <span>Wet-Bulb: {display_wb:.1f}{temp_unit}</span>
                    <span style="margin: 0 2px; color: #94A3B8;">•</span>
                    <span>ΔT: {abs(round(app_temp_c - wet_bulb_c, 1))}°C</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Card 2: Recommended Cooling Mode
    with col2:
        card_class = "success" if "Free-Air" in rec_mode else ("warning" if "Evaporative" in rec_mode else "danger")
        
        st.markdown(
            f"""
            <div class="kpi-card {card_class}">
                <div>
                    <div class="kpi-title">
                        <span>Cooling Dispatch</span>
                        <span style="font-size: 0.68rem; color: #64748B; font-weight: 700;">DECISION ENGINE</span>
                    </div>
                    <div style="margin-top: 6px; margin-bottom: 6px;">
                        {get_mode_badge_html(rec_mode)}
                    </div>
                </div>
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 500; margin-top: 4px;">
                    {kpis.get('eco_hours', 18)}/24 hrs eco-cooling active
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Card 3: PUE Efficiency Delta
    with col3:
        pue_delta_class = "delta-positive" if pue_delta_pct < 0 else "delta-neutral"
        
        st.markdown(
            f"""
            <div class="kpi-card highlight">
                <div>
                    <div class="kpi-title">
                        <span>Facility PUE</span>
                        <span style="font-size: 0.68rem; color: #0284C7; font-weight: 700;">EFFICIENCY</span>
                    </div>
                    <div class="kpi-value" style="color: {'#059669' if pue_delta_pct < 0 else '#0F172A'};">
                        {projected_pue:.2f}<span class="kpi-unit">Base: {baseline_pue:.2f}</span>
                    </div>
                </div>
                <div class="kpi-delta {pue_delta_class}">
                    <span>{pue_delta_pct:+.1f}% PUE Shift</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Card 4: Estimated Cost Savings
    with col4:
        st.markdown(
            f"""
            <div class="kpi-card success">
                <div>
                    <div class="kpi-title">
                        <span>Hourly Cost Savings</span>
                        <span style="font-size: 0.68rem; color: #059669; font-weight: 700;">REAL-TIME</span>
                    </div>
                    <div class="kpi-value" style="color: #059669;">
                        {format_currency(hourly_savings)}<span class="kpi-unit">/hr</span>
                    </div>
                </div>
                <div class="kpi-delta delta-positive">
                    <span>{hourly_kwh_saved:,.0f} kWh/hr Avoided</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Secondary Atmospheric & Sustainability Indicators Strip
    pm25_color = '#059669' if pm25 < 55 else ('#D97706' if pm25 < 65 else '#DC2626')
    st.markdown(
        f"""
        <div class="env-strip">
            <div class="env-item">
                <div class="env-item-label">Relative Humidity</div>
                <div class="env-item-value">{rh:.0f}%</div>
            </div>
            <div class="env-item">
                <div class="env-item-label">Air Quality (PM2.5)</div>
                <div class="env-item-value" style="color: {pm25_color};">
                    {int(pm25)} µg/m³
                </div>
            </div>
            <div class="env-item">
                <div class="env-item-label">CO2 Concentration</div>
                <div class="env-item-value">{int(co2_ppm)} ppm</div>
            </div>
            <div class="env-item">
                <div class="env-item-label">24h Cost Savings</div>
                <div class="env-item-value" style="color: #059669;">
                    {format_currency(kpis.get('total_savings_usd', 0.0))}
                </div>
            </div>
            <div class="env-item">
                <div class="env-item-label">Avoided Carbon</div>
                <div class="env-item-value" style="color: #059669;">
                    {kpis.get('total_co2_tons', 0.0):.2f} t CO₂e
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

