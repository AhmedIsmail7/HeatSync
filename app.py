"""FortyGuard – Data Center Cooling Intelligence Dashboard
Frontend Dashboard & Visual Analytics Layer.

Integrates the official HeatSync backend engines:
- FortyGuard API Ingestion & Cache Layer (David)
- LangGraph Decision Engine, Psychrometrics & Workload Dispatch (Ahmed)
- Streamlit Visual Dashboard & Geospatial Analytics (Ramy)
"""

from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Configure Streamlit Page
st.set_page_config(
    page_title="HeatSync | Data Center Cooling Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load CSS Stylesheet
css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Import Services and UI Components
from services.data_service import DataService
from components.sidebar import render_sidebar
from components.kpi_cards import render_kpi_cards
from components.timeline_chart import render_12h_timeline
from components.cooling_mode_view import render_cooling_mode_view
from components.alert_panel import render_alert_panel
from components.map_view import render_map_view
from components.comparison_view import render_comparison_view


def main():
    # Initialize Data Service
    data_service = DataService(mode="pipeline")
    facilities = data_service.get_facility_list()

    # Render Sidebar & retrieve interactive state
    selected_facility_id, selected_hour, temp_offset, unit_pref, sim_params = render_sidebar(facilities)

    # Fetch full analytics from HeatSync LangGraph pipeline
    analytics = data_service.get_full_analytics(
        facility_id=selected_facility_id,
        selected_hour=selected_hour,
        temp_offset=temp_offset,
    )

    if analytics.get("status") == "error":
        st.error("🚨 Live Telemetry Unreachable: The FortyGuard API is currently timing out. Please check your network connection or try again.")
        if st.button("🔄 Retry Connection"):
            st.rerun()
        st.stop()

    current_metrics = analytics["current_metrics"]
    kpis = analytics["kpis"]
    meta = analytics["facility_meta"]
    df_processed = analytics["processed_df"]
    alerts = analytics["alerts"]
    dispatch_rec = analytics["dispatch_recommendation"]
    narrative_text = analytics["narrative"]

    # Comparative benchmark & heat grid
    df_comparison = data_service.get_multi_facility_comparison(temp_offset=temp_offset)
    heat_grid = data_service.get_spatial_heat_grid(selected_facility_id)

    # Top Brand Header
    status_dot_color = '#059669' if current_metrics['recommended_mode'] != 'Mechanical Chiller (DX)' else '#DC2626'
    
    st.markdown(
        f"""
        <div class="fortyguard-header">
            <div>
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 3px;">
                    <span class="brand-badge">HeatSync</span>
                    <span style="font-size: 0.8rem; color: #94A3B8; font-weight: 500;">FortyGuard Microclimate Analytics</span>
                </div>
                <div style="font-size: 1.35rem; font-weight: 700; color: #F8FAFC; letter-spacing: -0.02em;">
                    {meta['name']}
                </div>
                <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 2px;">
                    <span>{meta.get('location', meta.get('name', 'USA'))}</span>
                    <span style="margin: 0 6px; color: #334155;">|</span>
                    <span>IT Capacity: <strong style="color: #F8FAFC;">{meta.get('it_load_mw', 10.0)} MW</strong></span>
                    <span style="margin: 0 6px; color: #334155;">|</span>
                    <span>Tariff: <strong style="color: #F8FAFC;">${meta.get('utility_rate_kwh', meta.get('electricity_rate_kwh', 0.085)):.3f}/kWh</strong></span>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="background: #0B0F19; border: 1px solid #1E293B; padding: 6px 14px; border-radius: 6px; text-align: right;">
                    <div style="display: flex; align-items: center; justify-content: flex-end; gap: 6px;">
                        <span class="pulse-dot" style="background-color: {status_dot_color};"></span>
                        <span style="font-weight: 700; font-size: 0.82rem; color: #F8FAFC;">Hour {current_metrics.get('timestamp', f'{selected_hour}:00')}</span>
                    </div>
                    <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 1px;">
                        Active Mode: <span style="font-weight: 600; color: #38BDF8;">{current_metrics['recommended_mode']}</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Main Tabbed Interface with Operations and Telemetry separated
    tab_ops, tab_tel, tab_geo, tab_bench, tab_arch = st.tabs([
        "Facility Operations",
        "Diurnal Telemetry",
        "Geospatial Heatmap",
        "Fleet Benchmarks",
        "System Architecture",
    ])

    # Tab 1: Facility Operations (Real-time KPIs, ASHRAE Diagnostics, AI Alerts)
    with tab_ops:
        # 1. Top KPI Metrics Cards + Workload Dispatch Banner
        render_kpi_cards(
            current_metrics=current_metrics,
            kpis=kpis,
            facility_meta=meta,
            unit_pref=unit_pref,
            dispatch_rec=dispatch_rec,
        )

        st.markdown("<div style='margin-top: 0.85rem;'></div>", unsafe_allow_html=True)

        # 2. AI Heat Risk Narrative & Operational Alerts Panel
        render_alert_panel(narrative_text, alerts, meta["name"])

    # Tab 2: Diurnal Telemetry (Timeline Chart & Hourly Data Inspection)
    with tab_tel:
        st.markdown("### 24-Hour Diurnal Telemetry & Atmospheric Profile")
        st.caption(f"Continuous microclimate forecast and automated cooling dispatch schedule for **{meta['name']}**.")

        # 1. 24-Hour Forecast Interactive Timeline Chart
        render_12h_timeline(df_processed, unit_pref=unit_pref, selected_hour=selected_hour)

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        # 2. Hourly Telemetry Inspection Table
        st.markdown("#### Hourly Telemetry Data Log")
        
        telemetry_cols = [
            "timestamp",
            "apparent_temperature_celsius",
            "wet_bulb_temperature_celsius",
            "relative_humidity_percent",
            "air_quality_pm2p5_idx",
            "recommended_mode",
            "projected_pue",
            "hourly_cost_saved_usd",
        ]
        
        # Ensure available columns exist in df_processed
        available_tel_cols = [c for c in telemetry_cols if c in df_processed.columns]
        df_tel_display = df_processed[available_tel_cols].copy()
        
        st.dataframe(
            df_tel_display,
            column_config={
                "timestamp": st.column_config.TextColumn("Timestamp", width="small"),
                "apparent_temperature_celsius": st.column_config.NumberColumn("Apparent Temp", format="%.1f °C"),
                "wet_bulb_temperature_celsius": st.column_config.NumberColumn("Wet-Bulb Temp", format="%.1f °C"),
                "relative_humidity_percent": st.column_config.NumberColumn("Humidity", format="%.0f%%"),
                "air_quality_pm2p5_idx": st.column_config.NumberColumn("AQI (PM2.5)", format="%d"),
                "recommended_mode": st.column_config.TextColumn("Dispatched Mode", width="medium"),
                "projected_pue": st.column_config.NumberColumn("PUE", format="%.2f"),
                "hourly_cost_saved_usd": st.column_config.NumberColumn("Savings ($/hr)", format="$%.2f"),
            },
            width="stretch",
            hide_index=True,
        )

    # Tab 3: Geospatial & Heatmap
    with tab_geo:
        st.markdown("### Geospatial Telemetry & Thermal Microclimate Heatmap")
        st.caption("3D geospatial rendering of facility IT capacity density and surrounding urban heat island temperature gradients.")

        map_mode = st.radio(
            "Perspective View",
            options=["Continental Overview (Fleet)", "Focused Facility Microclimate (Heat Island Layer)"],
            horizontal=True,
            index=0,
            label_visibility="collapsed",
        )
        selected_mode_key = "focused_microclimate" if "Focused" in map_mode else "3d_facility_overview"

        render_map_view(
            facilities=facilities,
            selected_facility_id=selected_facility_id,
            heat_grid_points=heat_grid,
            view_mode=selected_mode_key,
        )

    # Tab 4: Multi-Facility Comparison Benchmarks
    with tab_bench:
        render_comparison_view(df_comparison)

    # Tab 5: Pipeline Architecture & API Telemetry
    with tab_arch:
        st.markdown("### HeatSync Multi-Layer Architecture & Integration Hub")
        st.caption("End-to-end data pipeline flow and live LangGraph decision payloads.")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                """
                <div class="kpi-card highlight">
                    <div style="font-weight: 700; font-size: 0.92rem; color: #F8FAFC; margin-bottom: 4px;">1. Ingestion & Cache</div>
                    <div style="font-size: 0.8rem; color: #94A3B8; line-height: 1.5;">
                        • FortyGuard API Client (<code>/v1/env_params</code>)<br>
                        • JSON Caching: Ashburn, Phoenix, San Jose<br>
                        • Schema Standardization (Pandas)<br>
                        <span style="color: #10B981; font-weight: 600;">Status: Connected</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                """
                <div class="kpi-card highlight">
                    <div style="font-weight: 700; font-size: 0.92rem; color: #F8FAFC; margin-bottom: 4px;">2. Decision Engine</div>
                    <div style="font-size: 0.8rem; color: #94A3B8; line-height: 1.5;">
                        • ASHRAE Economizer Classification<br>
                        • PUE & Cost/CO₂ Energy Modeling<br>
                        • LangGraph 6-Node Orchestration<br>
                        <span style="color: #10B981; font-weight: 600;">Status: Operational</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c3:
            st.markdown(
                """
                <div class="kpi-card highlight">
                    <div style="font-weight: 700; font-size: 0.92rem; color: #F8FAFC; margin-bottom: 4px;">3. Frontend & Visuals</div>
                    <div style="font-size: 0.8rem; color: #94A3B8; line-height: 1.5;">
                        • Minimal Enterprise Dark Dashboard<br>
                        • Interactive Diurnal Plotly Charts<br>
                        • PyDeck 3D Geospatial Visuals<br>
                        <span style="color: #38BDF8; font-weight: 600;">Status: Active</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)
        with st.expander("Inspect Live Pipeline State Schema (JSON Payload)", expanded=False):
            st.caption("Live structured state output from the LangGraph 6-node decision graph at the active evaluation hour.")
            sample_json = {
                "facility_name": meta["name"],
                "selected_hour": selected_hour,
                "current_metrics": {
                    "apparent_temp": current_metrics["apparent_temperature_celsius"],
                    "wet_bulb": current_metrics["wet_bulb_temperature_celsius"],
                    "pm25": current_metrics["air_quality_pm2p5_idx"],
                    "mode": current_metrics["recommended_mode"],
                    "projected_pue": current_metrics["projected_pue"],
                    "hourly_cost_saved_usd": current_metrics["hourly_cost_saved_usd"],
                },
                "kpis": kpis,
                "alerts": alerts,
                "dispatch_recommendation": dispatch_rec,
            }
            st.json(sample_json)


if __name__ == "__main__":
    main()
