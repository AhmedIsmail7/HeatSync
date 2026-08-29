"""FortyGuard / HeatSync AI Operational Narrative & Alert Component.

Renders generative operational briefings (LangChain / Gemini) and
rule-based forecast alert triggers (Critical Chiller Peaks, Air Quality cutoffs).
"""

import re
from typing import Any, Dict, List
import streamlit as st


SEVERITY_STYLES = {
    "info": {"badge": "INFO", "class": "alert-info", "color": "#0284C7", "icon": "ℹ️"},
    "warning": {"badge": "WARNING", "class": "alert-warning", "color": "#F59E0B", "icon": "⚠️"},
    "critical": {"badge": "CRITICAL", "class": "alert-critical", "color": "#EF4444", "icon": "🚨"},
}


def format_markdown_to_html(text: str) -> str:
    """Helper to convert basic markdown (bold, italic, lists) into clean HTML."""
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = text.replace('\n\n', '<div style="margin-top: 0.55rem;"></div>').replace('\n', '<br>')
    return text


def render_alert_panel(narrative_text: str, alerts: List[Dict[str, Any]], facility_name: str) -> None:
    """Render the AI Operational Narrative and Actionable Alerts Panel."""
    formatted_narrative = format_markdown_to_html(narrative_text)

    st.markdown(
        f"""
        <div class="ai-narrative-card">
            <div class="ai-header">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="ai-badge">🤖 HeatSync AI Copilot</span>
                    <span style="font-size: 0.75rem; color: #64748B; font-weight: 600;">Gemini 3.7 Flash + LangGraph Orchestration</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span style="font-size: 0.78rem; font-weight: 700; color: #475569;">Facility:</span>
                    <span style="background: #E0F2FE; color: #0369A1; padding: 2px 10px; border-radius: 9999px; font-size: 0.78rem; font-weight: 800;">
                        {facility_name}
                    </span>
                </div>
            </div>
            <div style="font-size: 0.88rem; color: #1E293B; line-height: 1.6; margin-top: 0.5rem;">
                {formatted_narrative}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Render Active Alert Items
    if alerts:
        st.markdown(
            f"<div style='font-size: 0.92rem; font-weight: 700; color: #0F172A; margin: 0.85rem 0 0.5rem 0;'>"
            f"🚨 12-Hour Forecast Alerts ({len(alerts)} Triggered)</div>",
            unsafe_allow_html=True,
        )
        
        for alt in alerts:
            sev_key = alt.get("severity", "info").lower()
            sev_cfg = SEVERITY_STYLES.get(sev_key, SEVERITY_STYLES["info"])
            
            st.markdown(
                f"""
                <div class="alert-item {sev_cfg['class']}">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="font-size: 0.95rem;">{sev_cfg['icon']}</span>
                            <span style="font-weight: 700; font-size: 0.88rem; color: #0F172A;">{alt['title']}</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 0.72rem; color: #64748B; font-weight: 600;">Time: {alt.get('timestamp', '')}</span>
                            <span style="background: {sev_cfg['color']}; color: white; padding: 1px 6px; border-radius: 4px; font-size: 0.65rem; font-weight: 800;">
                                {sev_cfg['badge']}
                            </span>
                        </div>
                    </div>
                    <div style="font-size: 0.82rem; color: #334155; margin-bottom: 2px;">
                        {alt['message']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 0.65rem 1rem; font-size: 0.82rem; color: #166534; margin-top: 0.5rem;">
                ✅ <strong>Zero Thermal Alerts:</strong> No critical heat spikes or particulate cutoff events projected in the next 12 hours.
            </div>
            """,
            unsafe_allow_html=True,
        )
