"""FortyGuard / HeatSync AI Operational Narrative & Alert Component.

Renders generative operational briefings (LangChain / Gemini) and
rule-based forecast alert triggers (Critical Chiller Peaks, Air Quality cutoffs).
"""

import re
from typing import Any, Dict, List
import streamlit as st
from utils.helpers import SEVERITY_MAP


def format_markdown_to_html(text: str) -> str:
    """Helper to convert basic markdown (bold, italic, lists) into clean HTML."""
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = text.replace('\n\n', '<div style="margin-top: 0.5rem;"></div>').replace('\n', '<br>')
    return text


def render_alert_panel(narrative_text: str, alerts: List[Dict[str, Any]], facility_name: str) -> None:
    """Render the AI Operational Narrative and Actionable Alerts Panel."""
    formatted_narrative = format_markdown_to_html(narrative_text)

    st.markdown(
        f"""
        <div class="kpi-card" style="padding: 1.25rem; margin-bottom: 0.75rem;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; border-bottom: 1px solid #F1F5F9; padding-bottom: 0.5rem;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 0.88rem; font-weight: 700; color: #0F172A;">Operational Intelligence Briefing</span>
                    <span style="background: #F1F5F9; color: #64748B; font-size: 0.7rem; font-weight: 600; padding: 2px 7px; border-radius: 4px;">
                        LangGraph Orchestrated
                    </span>
                </div>
                <div style="font-size: 0.76rem; color: #64748B;">
                    Target: <span style="font-weight: 600; color: #0F172A;">{facility_name}</span>
                </div>
            </div>
            <div style="font-size: 0.84rem; color: #334155; line-height: 1.6;">
                {formatted_narrative}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Render Active Alert Items
    if alerts:
        st.markdown(
            f"<div style='font-size: 0.85rem; font-weight: 700; color: #0F172A; margin: 0.75rem 0 0.4rem 0; text-transform: uppercase; letter-spacing: 0.04em;'>"
            f"Active Forecast Alerts ({len(alerts)})</div>",
            unsafe_allow_html=True,
        )
        
        for alt in alerts:
            sev_key = alt.get("severity", "info").lower()
            sev_cfg = SEVERITY_MAP.get(sev_key, SEVERITY_MAP["info"])
            
            st.markdown(
                f"""
                <div class="alert-item {sev_cfg['class']}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                        <span style="font-weight: 700; font-size: 0.84rem; color: #0F172A;">{alt['title']}</span>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="font-size: 0.72rem; color: #64748B;">{alt.get('timestamp', '')}</span>
                            <span style="background: {sev_cfg['color']}; color: white; padding: 1px 6px; border-radius: 3px; font-size: 0.65rem; font-weight: 700;">
                                {sev_cfg['badge']}
                            </span>
                        </div>
                    </div>
                    <div style="font-size: 0.8rem; color: #475569;">
                        {alt['message']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 6px; padding: 0.6rem 0.9rem; font-size: 0.8rem; color: #065F46; margin-top: 0.5rem;">
                <strong>Zero Active Alerts:</strong> No critical thermal spikes or particulate threshold exceedances projected in the next 12 hours.
            </div>
            """,
            unsafe_allow_html=True,
        )

