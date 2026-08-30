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
        transition_info = f"Next transition projected at <strong>{next_switch['timestamp']}</strong> ➔ <strong>{next_switch['recommended_mode']}</strong>"
    else:
        transition_info = "No cooling mode transitions projected for the remainder of the 24-hour cycle."

    col_left, col_right = st.columns([1.1, 1.0])

    with col_left:
        import textwrap
        html_content = textwrap.dedent(f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.25rem; height: 100%; box-shadow: var(--shadow-sm);">
                <div style="font-size: 0.8rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 0.5rem;">
                    Strategy Diagnostic & ASHRAE Rationale
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                    <div>
                        <div style="font-size: 1.1rem; font-weight: 800; color: #0F172A;">Recommended State:</div>
                        <div style="margin-top: 4px;">{get_mode_badge_html(rec_mode)}</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700;">
                            ASHRAE TC 9.9 Compliance
                        </span>
                    </div>
                </div>
                <div style="font-size: 0.86rem; color: #334155; line-height: 1.5; margin-bottom: 1rem;">
                    <strong>Decision Engine Logic:</strong><br>
                    <span style="color: #0F172A; font-weight: 600;">{mode_reason}</span>
                    <ul style="margin: 0.45rem 0 0 1.15rem; padding: 0; font-size: 0.82rem;">
                        <li><strong>Apparent Temp ({app_temp:.1f}°C):</strong> {'≤ 19.0°C (Direct Free-Air Safe)' if app_temp <= 19.0 else ('≤ 27.0°C (Evaporative Viable)' if app_temp <= 27.0 else '> 27.0°C (Forces Mechanical DX)')}</li>
                        <li><strong>Wet-Bulb Temp ({wet_bulb:.1f}°C):</strong> {'≤ 18.5°C (Adiabatic Heat Rejection Enabled)' if wet_bulb <= 18.5 else '> 18.5°C (Chiller Compressors Mandatory)'}</li>
                        <li><strong>Particulate PM2.5 ({int(pm25)}):</strong> {'Safe intake threshold (< 55)' if pm25 < 55 else 'Filter protection cutoff triggered'}</li>
                    </ul>
                </div>
                <div style="background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 8px; padding: 0.65rem 0.9rem; font-size: 0.82rem; color: #0369A1;">
                    ⏱️ <strong>Transition Forecast:</strong> {transition_info}
                </div>
            </div>
        """)
        st.markdown(html_content, unsafe_allow_html=True)

    with col_right:
        # Psychrometric Envelope Chart
        fig_ashrae = go.Figure()

        # A2 Allowable Envelope Box
        fig_ashrae.add_shape(
            type="rect",
            x0=10, y0=8, x1=35, y1=80,
            line=dict(color="#CBD5E1", width=1.5, dash="dot"),
            fillcolor="rgba(241, 245, 249, 0.45)",
            layer="below",
        )
        
        # A1 Recommended Envelope Box
        fig_ashrae.add_shape(
            type="rect",
            x0=18, y0=8, x1=27, y1=60,
            line=dict(color="#10B981", width=2),
            fillcolor="rgba(209, 250, 229, 0.4)",
            layer="below",
        )

        # 24h Trajectory Points
        fig_ashrae.add_trace(
            go.Scatter(
                x=df_forecast["apparent_temperature_celsius"],
                y=df_forecast["relative_humidity_percent"],
                mode="lines+markers",
                name="24h Trajectory",
                line=dict(color="#0284C7", width=1.5, dash="dash"),
                marker=dict(size=5, color="#0284C7"),
                hoverinfo="skip",
            )
        )

        # Live Operating Point
        fig_ashrae.add_trace(
            go.Scatter(
                x=[app_temp],
                y=[rh],
                mode="markers+text",
                name="Current Hour Point",
                text=["📍 Active"],
                textposition="top center",
                marker=dict(size=12, color="#E11D48", symbol="diamond", line=dict(width=2, color="#FFFFFF")),
                hovertemplate=f"<b>Active Operating Point</b><br>Apparent Temp: {app_temp:.1f}°C<br>RH: {rh:.0f}%<extra></extra>",
            )
        )

        fig_ashrae.update_layout(
            title=dict(
                text="<b>Psychrometric Operating Envelope (ASHRAE TC 9.9)</b>",
                font=dict(size=13, color="#0F172A", family="Plus Jakarta Sans"),
            ),
            xaxis=dict(
                title="Apparent Temp (°C)",
                range=[5, 45],
                gridcolor="#F1F5F9",
                tickfont=dict(size=10, color="#64748B"),
            ),
            yaxis=dict(
                title="Relative Humidity (%)",
                range=[0, 100],
                gridcolor="#F1F5F9",
                tickfont=dict(size=10, color="#64748B"),
            ),
            margin=dict(l=35, r=15, t=35, b=30),
            height=240,
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            showlegend=False,
        )

        st.plotly_chart(fig_ashrae, use_container_width=True, config={"displayModeBar": False})
