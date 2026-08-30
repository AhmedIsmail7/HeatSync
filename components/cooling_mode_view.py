"""FortyGuard / HeatSync Cooling Mode Deep-Dive & ASHRAE Diagnostics.

Explains the recommended cooling mode (What, Why, When) based on
ASHRAE data center economizer rules and psychrometric envelopes.
"""

from typing import Any, Dict
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.helpers import get_mode_badge_html


def render_cooling_mode_view(current_metrics: Dict[str, Any], df_forecast: pd.DataFrame) -> None:
    """Render cooling strategy deep dive with ASHRAE economizer rules and psychrometric envelope."""
    rec_mode = current_metrics.get("recommended_mode", "Free-Air Economizer")
    mode_reason = current_metrics.get("mode_reason", "")
    app_temp = float(current_metrics.get("apparent_temperature_celsius", 22.0))
    wet_bulb = float(current_metrics.get("wet_bulb_temperature_celsius", 16.5))
    rh = float(current_metrics.get("relative_humidity_percent", 50.0))
    pm25 = float(current_metrics.get("air_quality_pm2p5_idx", 35.0))
    curr_hour = int(current_metrics.get("hour", 14))

    # Identify next upcoming mode switch
    future_df = df_forecast[df_forecast["hour"] > curr_hour]
    future_switches = future_df[future_df["recommended_mode"] != rec_mode]
    if not future_switches.empty:
        next_switch = future_switches.iloc[0]
        transition_info = f"Next mode transition projected at <strong>{next_switch['timestamp']}</strong> to <strong>{next_switch['recommended_mode']}</strong>"
    else:
        transition_info = "No cooling mode transitions projected for the remainder of the 24-hour cycle."

    col_left, col_right = st.columns([1.15, 1.0])

    with col_left:
        st.markdown(
            f"""
            <div class="kpi-card" style="padding: 1.25rem;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">
                    Strategy Diagnostic & ASHRAE Rationale
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.85rem;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 0.88rem; font-weight: 700; color: #F8FAFC;">Dispatch Mode:</span>
                        {get_mode_badge_html(rec_mode)}
                    </div>
                    <span style="background: #1E293B; color: #94A3B8; border: 1px solid #334155; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 600;">
                        ASHRAE TC 9.9
                    </span>
                </div>

                <div style="font-size: 0.82rem; color: #CBD5E1; line-height: 1.5; margin-bottom: 0.85rem;">
                    <div style="font-weight: 600; color: #F8FAFC; margin-bottom: 4px;">Engine Reasoning:</div>
                    <div style="color: #94A3B8;">{mode_reason}</div>
                    <div style="margin-top: 6px; padding-left: 0.75rem; border-left: 2px solid #334155; font-size: 0.78rem;">
                        <div>• Apparent Temp ({app_temp:.1f}°C): {'≤ 19.0°C (Direct Free-Air Economizer Safe)' if app_temp <= 19.0 else ('≤ 27.0°C (Evaporative Economizer Viable)' if app_temp <= 27.0 else '> 27.0°C (Forces Mechanical DX Chiller)')}</div>
                        <div>• Wet-Bulb Temp ({wet_bulb:.1f}°C): {'≤ 18.5°C (Adiabatic Heat Rejection Enabled)' if wet_bulb <= 18.5 else '> 18.5°C (Chiller Compressors Mandatory)'}</div>
                        <div>• Particulate PM2.5 ({int(pm25)}): {'Intake threshold safe (< 55 µg/m³)' if pm25 < 55 else 'Filter protection cutoff triggered'}</div>
                    </div>
                </div>

                <div style="background: #0B0F19; border: 1px solid #1E293B; border-radius: 6px; padding: 0.55rem 0.8rem; font-size: 0.78rem; color: #CBD5E1;">
                    <span style="font-weight: 600; color: #38BDF8;">Transition Forecast:</span> {transition_info}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        # Psychrometric Envelope Chart in Dark Mode
        fig_ashrae = go.Figure()

        # A2 Allowable Envelope Box
        fig_ashrae.add_shape(
            type="rect",
            x0=10, y0=8, x1=35, y1=80,
            line=dict(color="#334155", width=1, dash="dot"),
            fillcolor="rgba(30, 41, 59, 0.4)",
            layer="below",
        )
        
        # A1 Recommended Envelope Box
        fig_ashrae.add_shape(
            type="rect",
            x0=18, y0=8, x1=27, y1=60,
            line=dict(color="#10B981", width=1.5),
            fillcolor="rgba(16, 185, 129, 0.15)",
            layer="below",
        )

        # 24h Trajectory Points
        fig_ashrae.add_trace(
            go.Scatter(
                x=df_forecast["apparent_temperature_celsius"],
                y=df_forecast["relative_humidity_percent"],
                mode="lines+markers",
                name="24h Trajectory",
                line=dict(color="#38BDF8", width=1.5, dash="dash"),
                marker=dict(size=4, color="#38BDF8"),
                hoverinfo="skip",
            )
        )

        # Live Operating Point
        fig_ashrae.add_trace(
            go.Scatter(
                x=[app_temp],
                y=[rh],
                mode="markers+text",
                name="Current Point",
                text=["Active Point"],
                textposition="top center",
                marker=dict(size=9, color="#F8FAFC", symbol="circle", line=dict(width=1.5, color="#38BDF8")),
                textfont=dict(color="#F8FAFC", size=10),
                hovertemplate=f"Apparent Temp: {app_temp:.1f}°C<br>Relative Humidity: {rh:.0f}%<extra></extra>",
            )
        )

        fig_ashrae.update_layout(
            title=dict(
                text="<b>Psychrometric Envelope (ASHRAE TC 9.9)</b>",
                font=dict(size=12, color="#F8FAFC", family="Inter, sans-serif"),
            ),
            xaxis=dict(
                title="Apparent Temp (°C)",
                range=[5, 45],
                gridcolor="#1E293B",
                linecolor="#334155",
                tickfont=dict(size=10, color="#94A3B8"),
            ),
            yaxis=dict(
                title="Relative Humidity (%)",
                range=[0, 100],
                gridcolor="#1E293B",
                linecolor="#334155",
                tickfont=dict(size=10, color="#94A3B8"),
            ),
            margin=dict(l=35, r=15, t=35, b=30),
            height=250,
            plot_bgcolor="#111827",
            paper_bgcolor="#111827",
            showlegend=False,
        )

        st.plotly_chart(fig_ashrae, use_container_width=True, config={"displayModeBar": False})

