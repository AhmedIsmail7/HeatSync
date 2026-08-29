"""FortyGuard – Data Center Cooling Intelligence Dashboard
Frontend Dashboard & Visual Analytics Layer (Ramy).

Integrates the official HeatSync backend engines:
- FortyGuard API Ingestion & Cache Layer (David)
- LangGraph Decision Engine, Psychrometrics & Workload Dispatch (Ahmed)
- Streamlit Visual Dashboard & Geospatial Analytics (Ramy)
"""

from pathlib import Path
import streamlit as st

# Configure Streamlit Page
st.set_page_config(
    page_title="HeatSync – FortyGuard Cooling Intelligence",
    page_icon="❄️",
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

    # Top Brand Header Banner
    st.markdown(
        f"""
        <div class="fortyguard-header">
            <div>
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
                    <span class="brand-badge">HeatSync Intelligence</span>
                    <span style="font-size: 0.82rem; color: #64748B; font-weight: 600;">Powered by FortyGuard Microclimate API</span>
                </div>
                <div style="font-size: 1.45rem; font-weight: 800; color: #0F172A;">
                    {meta['name']}
                </div>
                <div style="font-size: 0.85rem; color: #475569; margin-top: 2px;">
                    📍 {meta['location']} &nbsp;•&nbsp; ⚡ IT Load: <strong>{meta['it_load_mw']} MW</strong> &nbsp;•&nbsp; 🌐 Utility Tariff: <strong>${meta['utility_rate_kwh']:.3f}/kWh</strong>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="display: inline-flex; align-items: center; gap: 8px; background: #FFFFFF; border: 1px solid #BAE6FD; padding: 6px 14px; border-radius: 9999px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <span class="pulse-dot" style="color: {'#10B981' if current_metrics['recommended_mode'] != 'Mechanical Chiller (DX)' else '#EF4444'};"></span>
                    <span style="font-weight: 700; font-size: 0.82rem; color: #0F172A;">Operating Hour: {current_metrics.get('timestamp', f'{selected_hour}:00')}</span>
                </div>
                <div style="font-size: 0.75rem; color: #64748B; margin-top: 5px;">
                    Mode: <strong>{current_metrics['recommended_mode']}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Main Tabbed Interface
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Facility Telemetry & Controls",
        "🗺️ Geospatial & Thermal Heatmap",
        "📈 Multi-Facility Fleet Benchmark",
        "⚙️ LangGraph Decision Telemetry",
    ])

    # Tab 1: Single Facility Operations
    with tab1:
        # 1. Top KPI Metrics Cards + Workload Dispatch Banner
        render_kpi_cards(
            current_metrics=current_metrics,
            kpis=kpis,
            facility_meta=meta,
            unit_pref=unit_pref,
            dispatch_rec=dispatch_rec,
        )

        st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)

        # 2. 24-Hour Forecast Interactive Timeline Chart
        render_12h_timeline(df_processed, unit_pref=unit_pref, selected_hour=selected_hour)

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        # 3. Cooling Strategy Deep Dive & ASHRAE Envelope
        render_cooling_mode_view(current_metrics, df_processed)

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        # 4. AI Heat Risk Narrative & Operational Alerts Panel
        render_alert_panel(narrative_text, alerts, meta["name"])

    # Tab 2: Geospatial & Heatmap
    with tab2:
        st.markdown("### 🗺️ Data Center Locations & Microclimate Thermal Heatmap")
        st.caption("3D geospatial rendering of facility IT load density and surrounding urban heat island (UHI) temperature gradients.")

        map_mode = st.radio(
            "Map Perspective",
            options=["Continental Overview (All Facilities)", "Focused Facility Microclimate (Heat Island Layer)"],
            horizontal=True,
            index=0,
        )
        selected_mode_key = "focused_microclimate" if "Focused" in map_mode else "3d_facility_overview"

        render_map_view(
            facilities=facilities,
            selected_facility_id=selected_facility_id,
            heat_grid_points=heat_grid,
            view_mode=selected_mode_key,
        )

    # Tab 3: Multi-Facility Comparison
    with tab3:
        render_comparison_view(df_comparison)

    # Tab 4: Pipeline Architecture & API Telemetry
    with tab4:
        st.markdown("### 🛠️ HeatSync Multi-Layer Architecture & Integration Hub")
        st.caption("Status and live payload schemas produced across our team roles.")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                """
                <div class="kpi-card highlight">
                    <div style="font-weight: 800; font-size: 1rem; color: #0F172A; margin-bottom: 4px;">1. Ingestion & Cache (David)</div>
                    <div style="font-size: 0.8rem; color: #475569; line-height: 1.4;">
                        • FortyGuard API Client (<code>/v1/env_params</code>)<br>
                        • JSON Caching: Ashburn, Phoenix, San José<br>
                        • Schema Standardization (Pandas)<br>
                        <span style="color: #10B981; font-weight: 700;">● Status: Connected</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                """
                <div class="kpi-card highlight">
                    <div style="font-weight: 800; font-size: 1rem; color: #0F172A; margin-bottom: 4px;">2. Decision Engine (Ahmed)</div>
                    <div style="font-size: 0.8rem; color: #475569; line-height: 1.4;">
                        • ASHRAE Economizer Classification<br>
                        • PUE & Cost/CO₂ Energy Modeling<br>
                        • LangGraph 6-Node Orchestration<br>
                        <span style="color: #10B981; font-weight: 700;">● Status: Operational</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c3:
            st.markdown(
                """
                <div class="kpi-card highlight">
                    <div style="font-weight: 800; font-size: 1rem; color: #0F172A; margin-bottom: 4px;">3. Frontend & Visuals (Ramy)</div>
                    <div style="font-size: 0.8rem; color: #475569; line-height: 1.4;">
                        • Streamlit Light/Sky-Blue Dashboard<br>
                        • Interactive Diurnal Plotly Horizon<br>
                        • PyDeck 3D Geospatial & Comparison<br>
                        <span style="color: #0284C7; font-weight: 700;">● Status: Active</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("#### Live Output State Schema (LangGraph Pipeline)")
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
