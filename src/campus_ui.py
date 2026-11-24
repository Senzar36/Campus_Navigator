"""A light, cartographic Plotly campus plan for the Streamlit frontend.

The coordinates are schematic. On the "All floors" view, separate panels
prevent locations on different floors from overlapping on screen.
"""
from __future__ import annotations

import html

import plotly.graph_objects as go

CANVAS = "#FAF9F5"
PAPER = "#FEFDF9"
INK = "#26352E"
SUBTLE = "#778178"
GRID = "#EAE7DF"
PATH = "#B65C3A"           # Terra-cotta: the chosen route
PATH_HALO = "rgba(182,92,58,0.19)"
FOOTPATH = "#C5C9BC"
FLOOR_LINK = "#9A947E"
START = "#2E6855"          # Forest: starting point
DESTINATION = "#A94232"    # Brick: destination
STUDENT = "#E5A12A"        # Ochre: moving agent
STOP = "#86734A"           # Bronze: intermediate stop

BUILDING_PALETTE = {
    "Main Block": "#3C6856",
    "CSE Block": "#A96643",
    "Food Block": "#888B5B",
    "Outdoor": "#857F91",
}


def floor_name(floor: int) -> str:
    return "GROUND FLOOR" if floor == 0 else f"FLOOR {floor:02d}"


def create_map(graph, path=None, current_step=None, floor_filter=None,
               start_id=None, destination_id=None, required_stops=None,
               show_labels=True):
    """Render all campus links, the selected route, and the student marker.

    The function signature is unchanged, so existing integration tests and
    callers continue to work after the visual redesign.
    """
    path = list(path or [])
    required_stops = list(required_stops or [])
    locations = graph.locations
    floors = sorted({int(value["floor"]) for value in locations.values()})
    all_floors = floor_filter is None

    xx = [data["x"] for data in locations.values()]
    yy = [data["y"] for data in locations.values()]
    left, right = min(xx), max(xx)
    bottom, top = min(yy), max(yy)
    panel_width = right - left + 16
    panel_height = top - bottom + 18

    def visible(node_id):
        return all_floors or int(locations[node_id]["floor"]) == floor_filter

    def offset(floor):
        if not all_floors:
            return 0, 0
        index = floors.index(int(floor))
        return (index % 2) * panel_width, -(index // 2) * panel_height

    def xy(node_id):
        node = locations[node_id]
        dx, dy = offset(node["floor"])
        return node["x"] + dx, node["y"] + dy

    figure = go.Figure()

    # Distinct, almost-paper-like panels make floors legible at first glance.
    if all_floors:
        for floor in floors:
            dx, dy = offset(floor)
            x0 = left + dx - 5.5
            x1 = right + dx + 5.5
            y0 = bottom + dy - 5.5
            y1 = top + dy + 5.5
            figure.add_shape(
                type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                fillcolor=PAPER,
                line=dict(color="#DDDCD2", width=1),
                layer="below",
            )
            figure.add_annotation(
                x=x0 + 1, y=y1 + 2.5,
                xanchor="left", yanchor="middle", showarrow=False,
                text=f"<b>{floor_name(floor)}</b>",
                font=dict(family="Arial", size=11, color="#53665A"),
            )

    # Draw only genuine edges from the existing backend graph.
    ordinary_x, ordinary_y = [], []
    transition_x, transition_y = [], []
    seen_edges = set()
    for src, neighbors in graph.adjacency_list.items():
        for dst, _weight in neighbors:
            edge_key = tuple(sorted((src, dst)))
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            if not visible(src) or not visible(dst):
                continue
            coords = (xy(src), xy(dst))
            floor_change = int(locations[src]["floor"]) != int(locations[dst]["floor"])
            xs, ys = (transition_x, transition_y) if floor_change else (ordinary_x, ordinary_y)
            xs.extend([coords[0][0], coords[1][0], None])
            ys.extend([coords[0][1], coords[1][1], None])

    figure.add_trace(go.Scatter(
        x=ordinary_x, y=ordinary_y, mode="lines",
        line=dict(color=FOOTPATH, width=2.4),
        hoverinfo="skip", showlegend=False,
    ))
    if transition_x:
        figure.add_trace(go.Scatter(
            x=transition_x, y=transition_y, mode="lines",
            line=dict(color=FLOOR_LINK, width=1.9, dash="dot"),
            name="Between floors", hoverinfo="skip",
        ))

    # Route highlight, with dotted segments for vertical floor changes.
    route_x, route_y = [], []
    vertical_x, vertical_y = [], []
    for src, dst in zip(path, path[1:]):
        if not visible(src) or not visible(dst):
            continue
        a, b = xy(src), xy(dst)
        floor_change = int(locations[src]["floor"]) != int(locations[dst]["floor"])
        xs, ys = (vertical_x, vertical_y) if floor_change else (route_x, route_y)
        xs.extend([a[0], b[0], None])
        ys.extend([a[1], b[1], None])

    if route_x:
        figure.add_trace(go.Scatter(
            x=route_x, y=route_y, mode="lines",
            line=dict(color=PATH_HALO, width=11),
            hoverinfo="skip", showlegend=False,
        ))
        figure.add_trace(go.Scatter(
            x=route_x, y=route_y, mode="lines",
            line=dict(color=PATH, width=4.5),
            name="Chosen route", hoverinfo="skip",
        ))
    if vertical_x:
        figure.add_trace(go.Scatter(
            x=vertical_x, y=vertical_y, mode="lines",
            line=dict(color=PATH, width=3.5, dash="dot"),
            name="Route · floor change", hoverinfo="skip",
        ))

    # Nodes grouped by building, preserving real location metadata on hover.
    for building in sorted({node["building"] for node in locations.values()}):
        identifiers = [key for key, node in locations.items()
                       if node["building"] == building and visible(key)]
        if not identifiers:
            continue
        values = [xy(node) for node in identifiers]
        figure.add_trace(go.Scatter(
            x=[value[0] for value in values],
            y=[value[1] for value in values],
            mode="markers+text" if show_labels else "markers",
            text=identifiers,
            textposition="top center",
            textfont=dict(size=10, color="#586A5C"),
            customdata=[[
                locations[node]["name"], locations[node]["building"],
                int(locations[node]["floor"]), locations[node]["type"], node,
            ] for node in identifiers],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Location code: %{customdata[4]}<br>"
                "Building: %{customdata[1]}<br>"
                "Floor: %{customdata[2]}<br>"
                "Type: %{customdata[3]}<extra></extra>"
            ),
            marker=dict(size=11, color=BUILDING_PALETTE.get(building, "#757D6F"),
                        line=dict(color="#FFFFFF", width=1.5)),
            name=building,
        ))

    def pin(node_id, name, color, symbol="circle", size=20):
        if not node_id or node_id not in locations or not visible(node_id):
            return
        x, y = xy(node_id)
        safe_name = html.escape(str(locations[node_id]["name"]))
        safe_id = html.escape(str(node_id))
        figure.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers",
            marker=dict(size=size, color=color, symbol=symbol,
                        line=dict(color="#FFFFFF", width=3)),
            name=name,
            hovertemplate=f"<b>{name}</b><br>{safe_name} ({safe_id})<extra></extra>",
        ))

    for stop in required_stops:
        pin(stop, "Required stop", STOP, symbol="square", size=16)
    pin(start_id, "Start", START, symbol="circle", size=20)
    pin(destination_id, "Destination", DESTINATION, symbol="diamond", size=20)
    if path and current_step is not None:
        index = min(max(int(current_step), 0), len(path) - 1)
        pin(path[index], "Student agent", STUDENT, symbol="star", size=24)

    max_x = max(xy(node)[0] for node in locations) if all_floors else right
    min_y = min(xy(node)[1] for node in locations) if all_floors else bottom
    figure.update_layout(
        height=550,
        paper_bgcolor=CANVAS, plot_bgcolor=CANVAS,
        margin=dict(l=12, r=12, t=34 if all_floors else 13, b=44),
        font=dict(family="Arial, sans-serif", color=INK),
        legend=dict(
            orientation="h", x=0, y=-0.10,
            xanchor="left", yanchor="top",
            font=dict(size=10, color="#6C786D"),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(bgcolor="#FFFFFF", font_color=INK,
                        bordercolor="#DFDDD2"),
        dragmode="pan", showlegend=True,
        xaxis=dict(
            visible=False, showgrid=True, gridcolor=GRID,
            scaleanchor="y", scaleratio=1,
            range=[left - 8, max_x + 8],
        ),
        yaxis=dict(visible=False, showgrid=True, gridcolor=GRID,
                   range=[min_y - 8, top + 10]),
        uirevision=f"campus-map-{floor_filter}",
    )
    return figure


def route_rows(graph, route, step):
    """Return human-friendly waypoints for a Streamlit table."""
    return [
        {
            "#": index + 1,
            "Location": graph.locations[node]["name"],
            "Building": graph.locations[node]["building"],
            "Floor": int(graph.locations[node]["floor"]),
            "Node": node,
            "Status": "Current" if index == step else
                      "Visited" if index < step else "Upcoming",
        }
        for index, node in enumerate(route)
    ]
