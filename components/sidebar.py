"""FortyGuard / HeatSync Sidebar Component.

Contains facility switcher, facility hardware/infrastructure profile,
operational hour selector, simulation controls, and data layer pipeline telemetry.
"""

from typing import Any, Dict, List, Tuple
import streamlit as st


def render_sidebar(facilities: List[Dict[str, Any]]) -> Tuple[str, int, float, str, Dict[str, Any]]:
    """Render the sidebar and return (selected_facility_id, selected_hour, temp_offset, unit_pref, simulation_params)."""
    with st.sidebar:
        # Branding Header
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 1.25rem;">
                <div style="background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%); width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 1.15rem; box-shadow: 0 2px 8px rgba(2, 132, 199, 0.35);">
                    ⚡
                </div>
                <div>
                    <div style="font-weight: 800; font-size: 1.15rem; color: #0F172A; line-height: 1.1;">HeatSync AI</div>
                    <div style="font-size: 0.72rem; color: #64748B; font-weight: 600;">Powered by FortyGuard Intelligence</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Facility Switcher Section
        st.markdown("### 🏢 Facility Selection")
        facility_names = {f["id"]: f"{f['name']} ({f['city']})" for f in facilities}
        facility_ids = list(facility_names.keys())

        # Persist selection in session state
        if "selected_facility_id" not in st.session_state:
            st.session_state.selected_facility_id = facility_ids[0]

        selected_id = st.selectbox(
            "Active Data Center Facility",
            options=facility_ids,
            format_func=lambda x: facility_names[x],
            index=facility_ids.index(st.session_state.selected_facility_id)
            if st.session_state.selected_facility_id in facility_ids
            else 0,
            key="facility_select_box",
        )
        st.session_state.selected_facility_id = selected_id

        # Selected Facility Metadata Card
        selected_fac = next(f for f in facilities if f["id"] == selected_id)
        
        status_bg = "#ECFDF5" if "Operational" in selected_fac["status"] else "#FFFBEB"
        status_text = "#065F46" if "Operational" in selected_fac["status"] else "#92400E"

        st.markdown(
            f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 0.85rem; margin: 0.75rem 0 1.25rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-size: 0.75rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Facility Telemetry</span>
                    <span style="background: {status_bg}; color: {status_text}; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 9999px;">
                        ● {selected_fac['status']}
                    </span>
                </div>
                <div style="font-size: 0.82rem; color: #334155; margin-bottom: 4px;">
                    <strong>Location:</strong> {selected_fac['city']}
                </div>
                <div style="font-size: 0.82rem; color: #334155; margin-bottom: 4px;">
                    <strong>Coordinates:</strong> <code>{selected_fac['lat']:.4f}° N, {abs(selected_fac['lon']):.4f}° W</code>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; color: #334155; margin-bottom: 4px;">
                    <span><strong>IT Load:</strong> <span style="color: #0284C7; font-weight: 700;">{selected_fac['it_load_mw']} MW</span></span>
                    <span><strong>Tariff:</strong> <span>${selected_fac['electricity_cost_kwh']:.3f}/kWh</span></span>
                </div>
                <div style="font-size: 0.78rem; color: #64748B; margin-top: 6px; border-top: 1px dashed #CBD5E1; padding-top: 4px;">
                    <strong>Cooling:</strong> {selected_fac['cooling_infrastructure']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Operational Timeline Hour Scrubber
        st.markdown("### 🕒 Operational Time Scrubber")
        selected_hour = st.slider(
            "Evaluation Hour (24h Diurnal Cycle)",
            min_value=0,
            max_value=23,
            value=14,
            format="%02d:00",
            help="Simulate the real-time operational decision state at different hours of the diurnal cycle.",
        )

        st.markdown("---")

        # Global Display & Unit Settings
        st.markdown("### ⚙️ Preferences & Simulation")
        unit_pref = st.radio(
            "Temperature Units",
            options=["Celsius (°C)", "Fahrenheit (°F)"],
            horizontal=True,
            index=0,
        )

        temp_offset = st.slider(
            "Ambient Temp Offset (Δ°C)",
            min_value=-5.0,
            max_value=10.0,
            value=0.0,
            step=0.5,
            help="Apply a thermal anomaly to test decision engine resilience and switching thresholds.",
        )

        st.markdown("---")

        # Pipeline Health Status
        st.markdown("### 🔌 HeatSync Pipeline Status")
        st.markdown(
            """
            <div style="font-size: 0.78rem; color: #475569;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>FortyGuard Ingestion (David)</span>
                    <span style="color: #10B981; font-weight: 700;">● Active (JSON Cache)</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>LangGraph Engine (Ahmed)</span>
                    <span style="color: #10B981; font-weight: 700;">● 6 Nodes Compiled</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>Visual Analytics (Ramy)</span>
                    <span style="color: #0284C7; font-weight: 700;">● Synchronized</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected_id, selected_hour, temp_offset, unit_pref, {}
