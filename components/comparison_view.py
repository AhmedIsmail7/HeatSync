"""FortyGuard Multi-Facility Comparison Component.

Renders side-by-side screening matrices (DATS style), comparative efficiency
benchmarks, and fleet-wide cost/risk ranking visualizations.
"""

from typing import Any, Dict
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils.helpers import format_currency


def render_comparison_view(df_comparison: pd.DataFrame) -> None:
    """Render multi-facility comparison dashboard with highlight cards, table, and charts."""
    st.markdown("### Fleet-Wide Data Center Cooling Benchmarks")
    st.caption(
        "Side-by-side facility benchmarking identifying thermal risk, efficiency opportunities, and fleet energy savings."
    )

    # 1. Executive Fleet Summary Cards
    highest_risk_row = df_comparison.loc[df_comparison["Risk Score (1-100)"].idxmax()]
    highest_load_row = df_comparison.loc[df_comparison["IT Load (MW)"].idxmax()]
    best_pue_row = df_comparison.loc[df_comparison["Current PUE"].idxmin()]
    max_savings_row = df_comparison.loc[df_comparison["12h Projected Savings ($)"].idxmax()]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="kpi-card danger">
                <div class="kpi-title"><span>Highest Thermal Risk</span></div>
                <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin-bottom: 2px;">{highest_risk_row['Facility Name'].split('(')[0].strip()}</div>
                <div class="kpi-delta delta-negative">Score: {highest_risk_row['Risk Score (1-100)']}/100 ({highest_risk_row['Ambient Temp (°C)']}°C)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="kpi-card highlight">
                <div class="kpi-title"><span>Peak IT Demand</span></div>
                <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin-bottom: 2px;">{highest_load_row['Facility Name'].split('(')[0].strip()}</div>
                <div class="kpi-delta delta-neutral">IT Load: {highest_load_row['IT Load (MW)']} MW</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="kpi-card success">
                <div class="kpi-title"><span>Optimal Efficiency (PUE)</span></div>
                <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin-bottom: 2px;">{best_pue_row['Facility Name'].split('(')[0].strip()}</div>
                <div class="kpi-delta delta-positive">PUE {best_pue_row['Current PUE']:.2f} ({best_pue_row['PUE Delta']:+.2f})</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="kpi-card success">
                <div class="kpi-title"><span>Top 12h Cost Savings</span></div>
                <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin-bottom: 2px;">{max_savings_row['Facility Name'].split('(')[0].strip()}</div>
                <div class="kpi-delta delta-positive">{format_currency(max_savings_row['12h Projected Savings ($)'])} / 12h</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # 2. Native Streamlit Table with rich column configurations
    display_cols = [
        "Facility Name",
        "Location",
        "IT Load (MW)",
        "Ambient Temp (°C)",
        "RH (%)",
        "AQI",
        "Recommended Mode",
        "Baseline PUE",
        "Current PUE",
        "PUE Delta",
        "Current Savings ($/hr)",
        "12h Projected Savings ($)",
        "Risk Level",
    ]
    
    st.dataframe(
        df_comparison[display_cols],
        column_config={
            "Facility Name": st.column_config.TextColumn("Facility Name", width="medium"),
            "Location": st.column_config.TextColumn("Location"),
            "IT Load (MW)": st.column_config.NumberColumn("IT Load", format="%.1f MW"),
            "Ambient Temp (°C)": st.column_config.NumberColumn("Ambient Temp", format="%.1f °C"),
            "RH (%)": st.column_config.NumberColumn("RH", format="%.0f%%"),
            "AQI": st.column_config.NumberColumn("AQI", format="%d"),
            "Recommended Mode": st.column_config.TextColumn("Recommended Mode"),
            "Baseline PUE": st.column_config.NumberColumn("Base PUE", format="%.2f"),
            "Current PUE": st.column_config.NumberColumn("Current PUE", format="%.2f"),
            "PUE Delta": st.column_config.NumberColumn("PUE Delta", format="%+.2f"),
            "Current Savings ($/hr)": st.column_config.NumberColumn("Savings ($/hr)", format="$%.2f"),
            "12h Projected Savings ($)": st.column_config.NumberColumn("12h Savings", format="$%.0f"),
            "Risk Level": st.column_config.TextColumn("Risk Level"),
        },
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # 3. Comparative Visual Charts
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        # PUE Comparison Bar Chart
        fig_pue = go.Figure()
        fig_pue.add_trace(
            go.Bar(
                name="Baseline PUE (DX Chillers)",
                x=df_comparison["Facility Name"].apply(lambda x: x.split(" (")[0]),
                y=df_comparison["Baseline PUE"],
                marker_color="#CBD5E1",
            )
        )
        fig_pue.add_trace(
            go.Bar(
                name="FortyGuard Optimized PUE",
                x=df_comparison["Facility Name"].apply(lambda x: x.split(" (")[0]),
                y=df_comparison["Current PUE"],
                marker_color="#0284C7",
            )
        )
        fig_pue.update_layout(
            title="<b>PUE Comparison: Baseline vs Optimized</b>",
            font=dict(family="Inter, sans-serif", size=12, color="#0F172A"),
            barmode="group",
            height=280,
            margin=dict(l=30, r=20, t=35, b=30),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            legend=dict(orientation="h", y=1.18, x=0.5, xanchor="center", font=dict(size=11, color="#64748B")),
            xaxis=dict(tickfont=dict(size=10, color="#64748B"), linecolor="#E2E8F0"),
            yaxis=dict(range=[1.0, 1.6], gridcolor="#F1F5F9", linecolor="#E2E8F0", tickfont=dict(size=10, color="#64748B")),
        )
        st.plotly_chart(fig_pue, use_container_width=True, config={"displayModeBar": False})

    with col_c2:
        # Projected 12-Hour Financial Savings Bar Chart
        fig_sav = px.bar(
            df_comparison,
            x=df_comparison["Facility Name"].apply(lambda x: x.split(" (")[0]),
            y="12h Projected Savings ($)",
            text="12h Projected Savings ($)",
            color="Recommended Mode",
            color_discrete_map={
                "Free-Air Cooling": "#059669",
                "Free-Air Economizer": "#059669",
                "Direct Evaporative": "#0284C7",
                "Evaporative Cooling": "#0284C7",
                "Mechanical DX Cooling": "#DC2626",
                "Mechanical Chiller (DX)": "#DC2626",
            },
            title="<b>Projected 12-Hour Cost Savings ($ USD)</b>",
        )
        fig_sav.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
        fig_sav.update_layout(
            font=dict(family="Inter, sans-serif", size=12, color="#0F172A"),
            height=280,
            margin=dict(l=30, r=20, t=35, b=30),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            legend=dict(orientation="h", y=1.18, x=0.5, xanchor="center", font=dict(size=11, color="#64748B")),
            xaxis=dict(tickfont=dict(size=10, color="#64748B"), linecolor="#E2E8F0"),
            yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", tickfont=dict(size=10, color="#64748B")),
        )
        st.plotly_chart(fig_sav, use_container_width=True, config={"displayModeBar": False})

