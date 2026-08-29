"""FortyGuard Geospatial & 3D Thermal Heatmap Component.

Uses PyDeck to visualize multi-facility data centers with 3D column layers,
status indicators, and microclimate heat grid overlays.
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
    
    # Format facility pins list of dictionaries (pure python types for pydeck serialization)
    fac_records = []
    for f in facilities:
        is_sel = f["id"] == selected_facility_id
        fac_records.append({
            "name": str(f["name"]),
            "city": str(f["city"]),
            "lat": float(f["lat"]),
            "lon": float(f["lon"]),
            "it_load_mw": float(f["it_load_mw"]),
            "elevation": float(f["it_load_mw"] * 8000.0),
            "status": str(f["status"]),
            "mode": str(f["current_active_mode"]),
            "color": [2, 132, 199, 230] if not is_sel else [225, 29, 72, 255],
        })

    # 1. Facility 3D Column Layer
    facility_layer = pdk.Layer(
        "ColumnLayer",
        data=fac_records,
        get_position=["lon", "lat"],
        get_elevation="elevation",
        elevation_scale=1,
        radius=35000,
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
        get_color=[15, 23, 42, 255],
        pixel_offset=[0, -25],
        billboard=True,
    )

    # 3. Microclimate Heat Grid Layer around Selected Facility
    heat_layer = pdk.Layer(
        "HexagonLayer",
        data=heat_grid_points,
        get_position=["longitude", "latitude"],
        radius=400,
        elevation_scale=15,
        elevation_range=[10, 1500],
        extruded=True,
        get_fill_color="color",
        pickable=True,
        opacity=0.65,
    )

    # Set View State
    if view_mode == "focused_microclimate":
        view_state = pdk.ViewState(
            latitude=float(selected_fac["lat"]),
            longitude=float(selected_fac["lon"]),
            zoom=12.0,
            pitch=45,
            bearing=15,
        )
        layers = [heat_layer, facility_layer, label_layer]
    else:  # continental overview
        view_state = pdk.ViewState(
            latitude=37.5,
            longitude=-96.0,
            zoom=3.6,
            pitch=35,
            bearing=0,
        )
        layers = [facility_layer, label_layer]

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style="light",
        tooltip={
            "html": "<b>{name}</b><br><span>Location: {city}</span><br><span>IT Load: {it_load_mw} MW</span><br><span>Status: {status}</span>",
            "style": {"backgroundColor": "#0F172A", "color": "#FFFFFF", "fontSize": "12px", "borderRadius": "6px", "padding": "6px 10px"},
        },
    )

    st.pydeck_chart(deck, use_container_width=True)
