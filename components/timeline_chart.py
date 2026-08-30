"""FortyGuard / HeatSync 24-Hour Diurnal Forecast Timeline Component.

Plots ambient apparent temperature, wet-bulb temperature, relative humidity,
cooling mode transitions, and financial savings using Plotly.
"""

from typing import Any, Dict
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.helpers import c_to_f


def render_12h_timeline(df: pd.DataFrame, unit_pref: str = "Celsius (°C)", selected_hour: int = 14) -> None:
    """Render interactive Plotly dual-axis chart showing 24h diurnal forecast & mode transitions."""
    is_f = "Fahrenheit" in unit_pref
    temp_unit = "°F" if is_f else "°C"
    
    plot_df = df.copy()
    if is_f:
        plot_df["plot_app_temp"] = plot_df["apparent_temperature_celsius"].apply(c_to_f)
        plot_df["plot_wet_bulb"] = plot_df["wet_bulb_temperature_celsius"].apply(c_to_f)
    else:
        plot_df["plot_app_temp"] = plot_df["apparent_temperature_celsius"]
        plot_df["plot_wet_bulb"] = plot_df["wet_bulb_temperature_celsius"]

    # Identify mode transitions
    plot_df["prev_mode"] = plot_df["recommended_mode"].shift(1)
    plot_df["is_switch"] = (plot_df["recommended_mode"] != plot_df["prev_mode"]) & (plot_df["prev_mode"].notna())

    fig = go.Figure()

    # 1. Relative Humidity Area Fill on Secondary Axis
    fig.add_trace(
        go.Scatter(
            x=plot_df["timestamp"],
            y=plot_df["relative_humidity_percent"],
            name="Relative Humidity (%)",
            mode="lines",
            line=dict(width=1.5, color="rgba(2, 132, 199, 0.3)", dash="dot"),
            fill="tozeroy",
            fillcolor="rgba(224, 242, 254, 0.25)",
            yaxis="y2",
            hovertemplate="Relative Humidity: %{y:.0f}%<extra></extra>",
        )
    )

    # 2. Apparent Temperature Line
    fig.add_trace(
        go.Scatter(
            x=plot_df["timestamp"],
            y=plot_df["plot_app_temp"],
            name=f"Apparent Temp ({temp_unit})",
            mode="lines+markers",
            line=dict(color="#0284C7", width=2.5),
            marker=dict(size=6, color="#0284C7", symbol="circle", line=dict(width=1.5, color="#FFFFFF")),
            hovertemplate=(
                f"<b>Time</b>: %{{x}}<br>"
                f"<b>Apparent Temp</b>: %{{y:.1f}}{temp_unit}<br>"
                f"<b>Dispatch Mode</b>: %{{customdata[0]}}<br>"
                f"<b>PUE</b>: %{{customdata[1]:.2f}}<br>"
                f"<b>Hourly Savings</b>: $%{{customdata[2]:,.2f}}"
                "<extra></extra>"
            ),
            customdata=plot_df[["recommended_mode", "projected_pue", "hourly_cost_saved_usd"]].values,
        )
    )

    # 3. Wet-Bulb Temperature Line
    fig.add_trace(
        go.Scatter(
            x=plot_df["timestamp"],
            y=plot_df["plot_wet_bulb"],
            name=f"Wet-Bulb Temp ({temp_unit})",
            mode="lines",
            line=dict(color="#059669", width=1.8, dash="dash"),
            hovertemplate=f"Wet-Bulb Temp: %{{y:.1f}}{temp_unit}<extra></extra>",
        )
    )

    # 4. Vertical Marker for Currently Selected Hour
    selected_rows = plot_df[plot_df["hour"] == selected_hour]
    if not selected_rows.empty:
        curr_time_label = selected_rows.iloc[0]["timestamp"]
        curr_val = selected_rows.iloc[0]["plot_app_temp"]
        fig.add_vline(
            x=curr_time_label,
            line_width=2,
            line_dash="solid",
            line_color="#0F172A",
        )
        fig.add_annotation(
            x=curr_time_label,
            y=curr_val,
            text=f"Evaluation Hour ({curr_time_label})",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-35,
            bgcolor="#0F172A",
            font=dict(size=10, color="#FFFFFF", family="Inter, sans-serif"),
            opacity=0.9,
            borderpad=4,
        )

    # 5. Highlight Mode Switching Points
    switch_rows = plot_df[plot_df["is_switch"]]
    for _, s_row in switch_rows.iterrows():
        fig.add_vline(
            x=s_row["timestamp"],
            line_width=1.2,
            line_dash="dash",
            line_color="#DC2626" if "Mechanical" in s_row["recommended_mode"] else "#059669",
        )

    # Layout styling
    min_temp = plot_df["plot_app_temp"].min() - 2.0
    max_temp = plot_df["plot_app_temp"].max() + 4.0

    fig.update_layout(
        title=dict(
            text="<b>24-Hour Diurnal Forecast & Cooling Dispatch</b>",
            font=dict(size=13, color="#F8FAFC", family="Inter, sans-serif"),
            x=0.01,
            y=0.96,
        ),
        margin=dict(l=45, r=45, t=45, b=35),
        height=360,
        plot_bgcolor="#111827",
        paper_bgcolor="#111827",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#94A3B8"),
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#1E293B",
            linecolor="#334155",
            tickfont=dict(size=10, color="#94A3B8"),
        ),
        yaxis=dict(
            title=dict(text=f"Temperature ({temp_unit})", font=dict(size=11, color="#F8FAFC")),
            range=[min_temp, max_temp],
            showgrid=True,
            gridcolor="#1E293B",
            linecolor="#334155",
            tickfont=dict(size=10, color="#94A3B8"),
        ),
        yaxis2=dict(
            title=dict(text="Relative Humidity (%)", font=dict(size=11, color="#38BDF8")),
            range=[0, 100],
            overlaying="y",
            side="right",
            showgrid=False,
            tickfont=dict(size=10, color="#38BDF8"),
        ),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

