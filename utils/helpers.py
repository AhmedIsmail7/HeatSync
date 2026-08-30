"""FortyGuard Dashboard Utility and Helper Functions.

Provides psychrometric approximations, styling formatters, and ASHRAE
classification helpers.
"""

from __future__ import annotations
import math
from typing import Any, Dict, Tuple


# Cooling Mode Design Constants
MODE_COLORS = {
    "Free-Air Economizer": {"bg": "#ECFDF5", "border": "#A7F3D0", "text": "#065F46", "hex": "#059669"},
    "Free-Air Cooling": {"bg": "#ECFDF5", "border": "#A7F3D0", "text": "#065F46", "hex": "#059669"},
    "Direct Evaporative": {"bg": "#F0F9FF", "border": "#BAE6FD", "text": "#0369A1", "hex": "#0284C7"},
    "Evaporative Cooling": {"bg": "#F0F9FF", "border": "#BAE6FD", "text": "#0369A1", "hex": "#0284C7"},
    "Mechanical Chiller (DX)": {"bg": "#FEF2F2", "border": "#FECACA", "text": "#991B1B", "hex": "#DC2626"},
    "Mechanical DX Cooling": {"bg": "#FEF2F2", "border": "#FECACA", "text": "#991B1B", "hex": "#DC2626"},
}

RISK_LEVEL_COLORS = {
    "Safe": {"bg": "#ECFDF5", "border": "#A7F3D0", "text": "#065F46", "hex": "#059669"},
    "Moderate": {"bg": "#FFFBEB", "border": "#FDE68A", "text": "#92400E", "hex": "#D97706"},
    "Warning": {"bg": "#FFFBEB", "border": "#FDE68A", "text": "#92400E", "hex": "#D97706"},
    "High Risk": {"bg": "#FEF2F2", "border": "#FECACA", "text": "#991B1B", "hex": "#DC2626"},
    "Critical": {"bg": "#FEF2F2", "border": "#FECACA", "text": "#991B1B", "hex": "#DC2626"},
}

SEVERITY_MAP = {
    "info": {"badge": "INFO", "class": "alert-info", "color": "#0284C7"},
    "warning": {"badge": "WARNING", "class": "alert-warning", "color": "#D97706"},
    "critical": {"badge": "CRITICAL", "class": "alert-critical", "color": "#DC2626"},
}


def calculate_wet_bulb(dry_bulb_c: float, rh_pct: float) -> float:
    """Calculate approximate Wet-Bulb Temperature (°C) using Stull's formula (2011).
    Valid for RH 5% - 99% and T -20°C to 50°C.
    """
    t = float(dry_bulb_c)
    rh = max(1.0, min(100.0, float(rh_pct)))
    
    tw = (
        t * math.atan(0.151977 * math.sqrt(rh + 8.313659))
        + math.atan(t + rh)
        - math.atan(rh - 1.676331)
        + 0.00391838 * (rh ** 1.5) * math.atan(0.023101 * rh)
        - 4.686035
    )
    return round(tw, 1)


def calculate_dew_point(dry_bulb_c: float, rh_pct: float) -> float:
    """Calculate Dew Point (°C) using the Magnus-Tetens approximation."""
    a = 17.27
    b = 237.7
    rh = max(0.01, min(100.0, float(rh_pct))) / 100.0
    alpha = ((a * dry_bulb_c) / (b + dry_bulb_c)) + math.log(rh)
    dp = (b * alpha) / (a - alpha)
    return round(dp, 1)


def c_to_f(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return round((celsius * 9.0 / 5.0) + 32.0, 1)


def format_currency(value: float, decimals: int = 0) -> str:
    """Format numeric value into USD currency string."""
    if decimals == 0:
        return f"${int(round(value)):,}"
    return f"${value:,.{decimals}f}"


def format_co2(kg_co2: float) -> str:
    """Format CO2 mass in kg or metric tonnes."""
    if kg_co2 >= 1000:
        return f"{kg_co2 / 1000.0:.2f} t"
    return f"{kg_co2:.1f} kg"


def get_mode_badge_html(mode: str) -> str:
    """Generate HTML pill badge for cooling mode without emojis."""
    cfg = MODE_COLORS.get(mode, MODE_COLORS["Mechanical Chiller (DX)"])
    return (
        f'<span style="background-color: {cfg["bg"]}; color: {cfg["text"]}; '
        f'border: 1px solid {cfg["border"]}; padding: 3px 10px; border-radius: 9999px; '
        f'font-size: 0.8rem; font-weight: 700; display: inline-flex; align-items: center; gap: 6px;">'
        f'<span style="width: 7px; height: 7px; border-radius: 50%; background-color: {cfg["hex"]};"></span>'
        f'{mode}</span>'
    )


def get_risk_badge_html(risk_level: str) -> str:
    """Generate HTML badge for risk severity without emojis."""
    cfg = RISK_LEVEL_COLORS.get(risk_level, RISK_LEVEL_COLORS["High Risk"])
    return (
        f'<span style="background-color: {cfg["bg"]}; color: {cfg["text"]}; '
        f'border: 1px solid {cfg["border"]}; padding: 3px 9px; border-radius: 9999px; '
        f'font-size: 0.76rem; font-weight: 700; display: inline-flex; align-items: center; gap: 6px;">'
        f'<span style="width: 6px; height: 6px; border-radius: 50%; background-color: {cfg["hex"]};"></span>'
        f'{risk_level}</span>'
    )


def classify_ashrae_compliance(dry_bulb_c: float, rh_pct: float) -> Dict[str, Any]:
    """Check compliance against ASHRAE TC 9.9 Thermal Guidelines (A1 Recommended / Allowable).
    - Recommended A1: Dry-bulb 18°C to 27°C (64.4°F to 80.6°F), RH 8% to 60%, Dew Point -9°C to 15°C
    - Allowable A2: Dry-bulb 10°C to 35°C (50°F to 95°F), RH 8% to 80%, Dew Point -12°C to 17°C
    """
    dp = calculate_dew_point(dry_bulb_c, rh_pct)
    
    in_recommended = (18.0 <= dry_bulb_c <= 27.0) and (8.0 <= rh_pct <= 60.0) and (-9.0 <= dp <= 15.0)
    in_allowable = (10.0 <= dry_bulb_c <= 35.0) and (8.0 <= rh_pct <= 80.0) and (-12.0 <= dp <= 17.0)
    
    if in_recommended:
        return {
            "status": "ASHRAE A1 Recommended",
            "tier": "Optimal",
            "badge_color": "#059669",
            "desc": "Environmental conditions fall strictly within ASHRAE A1 optimal operating envelope."
        }
    elif in_allowable:
        return {
            "status": "ASHRAE A2 Allowable",
            "tier": "Sub-Optimal",
            "badge_color": "#D97706",
            "desc": "Operating in allowable envelope. Economizer or adiabatic trim cooling may be required."
        }
    else:
        return {
            "status": "Non-Compliant (Extreme)",
            "tier": "Critical Stress",
            "badge_color": "#DC2626",
            "desc": "Outside standard air-cooling envelopes. Full mechanical refrigeration required to prevent server throttling."
        }

