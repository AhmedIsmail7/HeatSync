"""FortyGuard / HeatSync Sidebar Component.

Contains facility switcher, facility hardware/infrastructure profile,
operational hour selector, simulation controls, and data layer pipeline telemetry.
Organized into clean tabs in the sidebar for optimal UX.
"""

from typing import Any, Dict, List, Tuple
import streamlit as st


def render_sidebar(facilities: List[Dict[str, Any]]) -> Tuple[str, int, float, str, Dict[str, Any]]:
    """Render the sidebar and return (selected_facility_id, selected_hour, temp_offset, unit_pref, simulation_params)."""
    with st.sidebar:
        # Minimal Branding Header
        st.markdown(
            """
            <div style="margin-bottom: 1rem;">
                <div style="font-size: 1.15rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.02em;">
                    HeatSync
                </div>
                <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 1px;">
                    FortyGuard Microclimate Intelligence
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Tabbed Sidebar Interface
        tab_nav, tab_sim, tab_sys = st.tabs([
            "Facility",
            "Simulation",
            "Telemetry",
        ])

        # TAB 1: Facility Navigation & Hardware Specifications
        with tab_nav:
            st.markdown('<div class="sidebar-section-title" style="margin-top: 0.5rem;">Active Data Center</div>', unsafe_allow_html=True)
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
            status_bg = "rgba(16, 185, 129, 0.12)" if is_op else "rgba(245, 158, 11, 0.12)"
            status_text = "#10B981" if is_op else "#F59E0B"
            status_border = "rgba(16, 185, 129, 0.3)" if is_op else "rgba(245, 158, 11, 0.3)"
            dot_color = "#10B981" if is_op else "#F59E0B"

            st.markdown(
                f"""
                <div style="background: #111827; border: 1px solid #1E293B; border-radius: 8px; padding: 0.85rem; margin-top: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 0.72rem; font-weight: 700; color: #94A3B8; text-transform: uppercase;">Status</span>
                        <span style="background: {status_bg}; color: {status_text}; border: 1px solid {status_border}; font-size: 0.7rem; font-weight: 700; padding: 1px 6px; border-radius: 9999px; display: inline-flex; align-items: center; gap: 4px;">
                            <span style="width: 5px; height: 5px; border-radius: 50%; background: {dot_color};"></span>
                            {selected_fac['status']}
                        </span>
                    </div>
                    <div style="font-size: 0.78rem; color: #CBD5E1; line-height: 1.7;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #94A3B8;">Location:</span>
                            <span style="font-weight: 600; color: #F8FAFC;">{selected_fac['city']}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #94A3B8;">Coordinates:</span>
                            <code style="color: #38BDF8; font-size: 0.72rem;">{selected_fac['lat']:.2f}°N, {abs(selected_fac['lon']):.2f}°W</code>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #94A3B8;">IT Load:</span>
                            <span style="font-weight: 600; color: #38BDF8;">{selected_fac['it_load_mw']} MW</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #94A3B8;">Electricity Tariff:</span>
                            <span style="font-weight: 600; color: #F8FAFC;">${selected_fac['electricity_cost_kwh']:.3f}/kWh</span>
                        </div>
                    </div>
                    <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid #1E293B; font-size: 0.72rem; color: #94A3B8; line-height: 1.4;">
                        <strong style="color: #CBD5E1;">Infrastructure:</strong> {selected_fac['cooling_infrastructure']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # TAB 2: Simulation Controls & Diurnal Scrubber
        with tab_sim:
            from datetime import datetime
            try:
                from zoneinfo import ZoneInfo
            except ImportError:
                from backports.zoneinfo import ZoneInfo

            tz_map = {
                "ASHBURN": "America/New_York",
                "PHOENIX": "America/Phoenix",
                "SANJOSE": "America/Los_Angeles",
            }
            fac_id = st.session_state.get("selected_facility_id", "ASHBURN").upper()
            tz_name = tz_map.get(fac_id, "UTC")
            current_local_hour = datetime.now(ZoneInfo(tz_name)).hour
            
            # Force slider to local time if facility changes or on first load
            if st.session_state.get("_last_fac_id") != fac_id:
                st.session_state["hour_scrubber_widget"] = current_local_hour
                st.session_state["_last_fac_id"] = fac_id
            
            st.markdown('<div class="sidebar-section-title" style="margin-top: 0.5rem;">Diurnal Time Scrubber</div>', unsafe_allow_html=True)
            selected_hour = st.slider(
                "Evaluation Hour (24h)",
                min_value=0,
                max_value=23,
                value=current_local_hour,
                format="%02d:00",
                key="hour_scrubber_widget",
                help="Evaluate decision state and atmospheric forecast across the diurnal cycle.",
                label_visibility="collapsed",
            )
            st.caption(f"Active Evaluation Hour: **{selected_hour:02d}:00**")

            st.markdown('<div class="sidebar-section-title" style="margin-top: 0.75rem;">Display Preferences</div>', unsafe_allow_html=True)
            unit_pref = st.radio(
                "Temperature Units",
                options=["Celsius (°C)", "Fahrenheit (°F)"],
                horizontal=True,
                index=0,
            )

            st.markdown('<div class="sidebar-section-title" style="margin-top: 0.75rem;">Thermal Stress Anomaly</div>', unsafe_allow_html=True)
            temp_offset = st.slider(
                "Ambient Temp Offset (Δ°C)",
                min_value=-5.0,
                max_value=10.0,
                value=0.0,
                step=0.5,
                help="Simulate thermal anomalies to test decision engine switching thresholds.",
            )

        # TAB 3: Pipeline & System Telemetry Status
        with tab_sys:
            st.markdown('<div class="sidebar-section-title" style="margin-top: 0.5rem;">Pipeline Layer Health</div>', unsafe_allow_html=True)
            st.markdown(
                """
                <div style="background: #111827; border: 1px solid #1E293B; border-radius: 8px; padding: 0.85rem; font-size: 0.75rem; color: #CBD5E1; line-height: 1.8;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                        <span>FortyGuard Ingestion:</span>
                        <span style="color: #10B981; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;">
                            <span style="width: 5px; height: 5px; border-radius: 50%; background: #10B981;"></span> Connected
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                        <span>LangGraph Engine:</span>
                        <span style="color: #10B981; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;">
                            <span style="width: 5px; height: 5px; border-radius: 50%; background: #10B981;"></span> 6 Nodes Active
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span>Visual Analytics:</span>
                        <span style="color: #38BDF8; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;">
                            <span style="width: 5px; height: 5px; border-radius: 50%; background: #38BDF8;"></span> Synced
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown('<div class="sidebar-section-title" style="margin-top: 0.75rem;">Microclimate API Source</div>', unsafe_allow_html=True)
            st.markdown(
                """
                <div style="font-size: 0.72rem; color: #94A3B8; line-height: 1.5;">
                    <div>• <strong style="color: #CBD5E1;">Provider:</strong> FortyGuard API</div>
                    <div>• <strong style="color: #CBD5E1;">Resolution:</strong> Hyperlocal Heat Grids</div>
                    <div>• <strong style="color: #CBD5E1;">Models:</strong> ASHRAE TC 9.9 + Gemini 3.7</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Sync Live Telemetry", use_container_width=True, help="Clear cache and fetch fresh API data"):
                st.cache_data.clear()
                st.rerun()

    return selected_id, selected_hour, temp_offset, unit_pref, {}


