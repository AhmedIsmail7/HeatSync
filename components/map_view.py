"""FortyGuard Geospatial & 3D Thermal Heatmap Component.

Uses PyDeck to visualize multi-facility data centers with 3D column layers,
status indicators, and microclimate heat grid overlays in dark mode.
"""

from typing import Any, Dict, List
import pydeck as pdk
import streamlit as st


def render_map_view(
    facilities: List[Dict[str, Any]],
    selected_facility_id: str,
    heat_grid_points: List[Dict[str, Any]],
    view_mode: str = "3d_facility_overview",
) -> None:
    """Render PyDeck 3D map with facility columns and localized thermal grid layer."""
    selected_fac = next(f for f in facilities if f["id"] == selected_facility_id)
    
    # Format facility records with glowing dark mode colors
    fac_records = []
    for f in facilities:
        is_sel = f["id"] == selected_facility_id
        fac_records.append({
            "name": str(f["name"]),
            "city": str(f["city"]),
            "lat": float(f["lat"]),
            "lon": float(f["lon"]),
            "it_load_mw": float(f["it_load_mw"]),
            "elevation": float(f["it_load_mw"] * 8500.0),
            "status": str(f["status"]),
            "mode": str(f["current_active_mode"]),
            "color": [56, 189, 248, 230] if is_sel else [100, 116, 139, 180],
            "radius": 32000 if not is_sel else 38000,
        })

    # 1. Facility 3D Column Layer
    facility_layer = pdk.Layer(
        "ColumnLayer",
        data=fac_records,
        get_position=["lon", "lat"],
        get_elevation="elevation",
        elevation_scale=1,
        radius=30000,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
    )

    # 2. Text / Label Layer for Facilities
    label_layer = pdk.Layer(
        "TextLayer",
        data=fac_records,
        get_position=["lon", "lat"],
        get_text="name",
        get_size=13,
        get_color=[248, 250, 252, 255],
        pixel_offset=[0, -28],
        billboard=True,
    )

    # 3. Microclimate Thermal Heat Grid Layer around Selected Facility
    heat_layer = pdk.Layer(
        "ColumnLayer",
        data=heat_grid_points,
        get_position=["longitude", "latitude"],
        get_elevation="elevation",
        elevation_scale=18,
        radius=250,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
        opacity=0.85,
    )

    # Set View State
    if view_mode == "focused_microclimate":
        view_state = pdk.ViewState(
            latitude=float(selected_fac["lat"]),
            longitude=float(selected_fac["lon"]),
            zoom=12.2,
            pitch=50,
            bearing=20,
        )
        layers = [heat_layer, facility_layer, label_layer]
    else:  # continental overview
        view_state = pdk.ViewState(
            latitude=37.8,
            longitude=-96.5,
            zoom=3.7,
            pitch=38,
            bearing=0,
        )
        layers = [facility_layer, label_layer]

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style="dark",
        tooltip={
            "html": "<div style='font-family: Inter, sans-serif; padding: 4px 6px;'>"
                    "<div style='font-weight: 700; font-size: 13px; color: #38BDF8; margin-bottom: 3px;'>{name}</div>"
                    "<div style='color: #94A3B8; font-size: 11px;'>Location: <span style='color: #F8FAFC; font-weight: 600;'>{city}</span></div>"
                    "<div style='color: #94A3B8; font-size: 11px;'>IT Load: <span style='color: #38BDF8; font-weight: 700;'>{it_load_mw} MW</span></div>"
                    "<div style='color: #94A3B8; font-size: 11px;'>Status: <span style='color: #10B981; font-weight: 600;'>{status}</span></div>"
                    "</div>",
            "style": {"backgroundColor": "#0F172A", "color": "#FFFFFF", "fontSize": "11px", "borderRadius": "8px", "padding": "8px 12px", "border": "1px solid #1E293B"},
        },
    )

    st.pydeck_chart(deck, use_container_width=True)

    # Geospatial Thermal Legend & Microclimate Stats Overlay
    c1, c2 = st.columns([1.5, 1.0])
    with c1:
        st.markdown(
            """
            <div class="map-legend-box">
                <div style="font-size: 0.72rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
                    Thermal Island Microclimate Gradient (°C)
                </div>
                <div style="display: flex; align-items: center; gap: 12px; font-size: 0.76rem; color: #CBD5E1;">
                    <div style="display: flex; align-items: center; gap: 5px;">
                        <span style="width: 10px; height: 10px; border-radius: 2px; background: #0D9488;"></span>
                        <span>&lt; 22°C (Free-Air)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 5px;">
                        <span style="width: 10px; height: 10px; border-radius: 2px; background: #0284C7;"></span>
                        <span>22 - 28°C (Evaporative)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 5px;">
                        <span style="width: 10px; height: 10px; border-radius: 2px; background: #F59E0B;"></span>
                        <span>28 - 36°C (Thermal Stress)</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 5px;">
                        <span style="width: 10px; height: 10px; border-radius: 2px; background: #EF4444;"></span>
                        <span>&gt; 36°C (Extreme DX)</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="map-legend-box">
                <div style="font-size: 0.72rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">
                    Active Focus: {selected_fac['name']}
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.76rem; color: #CBD5E1;">
                    <span>Coordinates: <code>{selected_fac['lat']:.2f}°N, {abs(selected_fac['lon']):.2f}°W</code></span>
                    <span>Grid Points: <strong style="color: #38BDF8;">{len(heat_grid_points)}</strong></span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


