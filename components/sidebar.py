"""FortyGuard / HeatSync Sidebar Component.

Contains facility switcher, facility hardware/infrastructure profile,
operational hour selector, simulation controls, and data layer pipeline telemetry.
"""

from typing import Any, Dict, List, Tuple
import streamlit as st


def render_sidebar(facilities: List[Dict[str, Any]]) -> Tuple[str, int, float, str, Dict[str, Any]]:
    """Render the sidebar and return (selected_facility_id, selected_hour, temp_offset, unit_pref, simulation_params)."""
    with st.sidebar:
        # Minimal Branding Header
        st.markdown(
            """
            <div style="margin-bottom: 1.25rem;">
                <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em;">
                    HeatSync
                </div>
                <div style="font-size: 0.72rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 1px;">
                    FortyGuard Microclimate Intelligence
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 1. Facility Switcher Section
        st.markdown('<div class="sidebar-section-title">Facility Navigation</div>', unsafe_allow_html=True)
        facility_names = {f["id"]: f"{f['name']} ({f['city']})" for f in facilities}
        facility_ids = list(facility_names.keys())

        # Persist selection in session state
        if "selected_facility_id" not in st.session_state:
            st.session_state.selected_facility_id = facility_ids[0]

        selected_id = st.selectbox(
            "Active Data Center",
            options=facility_ids,
            format_func=lambda x: facility_names[x],
            index=facility_ids.index(st.session_state.selected_facility_id)
            if st.session_state.selected_facility_id in facility_ids
            else 0,
            key="facility_select_box",
            label_visibility="collapsed",
        )
        st.session_state.selected_facility_id = selected_id

        selected_fac = next(f for f in facilities if f["id"] == selected_id)
        is_op = "Operational" in selected_fac["status"]
        status_bg = "#ECFDF5" if is_op else "#FFFBEB"
        status_text = "#065F46" if is_op else "#92400E"
        status_border = "#A7F3D0" if is_op else "#FDE68A"
        dot_color = "#059669" if is_op else "#D97706"

        # Facility Specs Details Expander
        with st.expander("Facility Specifications", expanded=False):
            st.markdown(
                f"""
                <div style="font-size: 0.78rem; color: #334155; line-height: 1.6;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #64748B;">Status:</span>
                        <span style="background: {status_bg}; color: {status_text}; border: 1px solid {status_border}; font-size: 0.7rem; font-weight: 700; padding: 1px 6px; border-radius: 9999px; display: inline-flex; align-items: center; gap: 4px;">
                            <span style="width: 5px; height: 5px; border-radius: 50%; background: {dot_color};"></span>
                            {selected_fac['status']}
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #64748B;">Location:</span>
                        <span style="font-weight: 600;">{selected_fac['city']}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #64748B;">Coordinates:</span>
                        <code>{selected_fac['lat']:.2f}°N, {abs(selected_fac['lon']):.2f}°W</code>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #64748B;">IT Load:</span>
                        <span style="font-weight: 600; color: #0284C7;">{selected_fac['it_load_mw']} MW</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #64748B;">Electricity Tariff:</span>
                        <span style="font-weight: 600;">${selected_fac['electricity_cost_kwh']:.3f}/kWh</span>
                    </div>
                    <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid #E2E8F0; font-size: 0.72rem; color: #64748B;">
                        <strong>Infrastructure:</strong> {selected_fac['cooling_infrastructure']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # 2. Operational Timeline Hour Scrubber
        st.markdown('<div class="sidebar-section-title">Diurnal Time Scrubber</div>', unsafe_allow_html=True)
        selected_hour = st.slider(
            "Evaluation Hour (24h)",
            min_value=0,
            max_value=23,
            value=14,
            format="%02d:00",
            help="Evaluate decision state and atmospheric forecast across the diurnal cycle.",
            label_visibility="collapsed",
        )
        st.caption(f"Active Evaluation Timestamp: **{selected_hour:02d}:00**")

        # 3. Global Display & Unit Settings
        st.markdown('<div class="sidebar-section-title">Preferences & Simulation</div>', unsafe_allow_html=True)
        unit_pref = st.radio(
            "Temperature Units",
            options=["Celsius (°C)", "Fahrenheit (°F)"],
            horizontal=True,
            index=0,
        )

        temp_offset = st.slider(
            "Thermal Stress Offset (Δ°C)",
            min_value=-5.0,
            max_value=10.0,
            value=0.0,
            step=0.5,
            help="Simulate thermal anomalies to test decision engine switching thresholds.",
        )

        # 4. Pipeline Health Status
        with st.expander("Pipeline Telemetry Status", expanded=False):
            st.markdown(
                """
                <div style="font-size: 0.75rem; color: #475569; line-height: 1.7;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>FortyGuard Ingestion:</span>
                        <span style="color: #059669; font-weight: 600;">Connected (Cache)</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>LangGraph Orchestration:</span>
                        <span style="color: #059669; font-weight: 600;">6 Nodes Active</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Visual Analytics Engine:</span>
                        <span style="color: #0284C7; font-weight: 600;">Synchronized</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    return selected_id, selected_hour, temp_offset, unit_pref, {}

