import os
import sys
import time
import mesa
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graph import CampusGraph
from pathfinding import PathFinder
from navigation import Navigator

st.set_page_config(page_title='Campus Navigator', page_icon='🧭', layout='wide')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@st.cache_resource
def load_graph():
    return CampusGraph(os.path.join(BASE_DIR, 'data', 'Campus_Navigator_Dataset.csv'),
                       os.path.join(BASE_DIR, 'data', 'campus_connections.csv'))

graph = load_graph()
pathfinder = PathFinder(graph)

navigator = Navigator(pathfinder)
locations = graph.locations
ids = list(locations)
floors = sorted({v['floor'] for v in locations.values()}, key=str)

class StudentAgent(mesa.Agent):
    def __init__(self, model, path):
        super().__init__(model)
        self.path = path
        self.current_step = 0
    def step(self):
        self.current_step = min(self.current_step + 1, len(self.path)-1)

class CampusModel(mesa.Model):
    def __init__(self, path):
        super().__init__()
        self.student = StudentAgent(self, path)
    def step(self):
        self.student.step()

if not ids:
    st.error('No campus locations found.')
    st.stop()

s = st.session_state
for key, value in dict(route=[], distance=0.0, simulation=None, running=False,
                       floor=locations[ids[0]]['floor'], follow=True, stops=[],
                       message='Choose your starting location and destination.',
                       planned=[], next_tick=0.0).items():
    if key not in s:
        s[key] = value

def label(node):
    return f"{locations[node]['name']} ({node})"

def floor_label(f):
    return 'Ground floor' if str(f) == '0' else f'Floor {f}'

def current_node():
    return s.simulation.student.path[s.simulation.student.current_step] if s.simulation is not None else None

def sync_floor():
    node = current_node()
    if node is not None and s.follow:
        s.floor = locations[node]['floor']
        s.manual_floor = s.floor

def calculate():
    s.running = False
    s.route, s.distance, s.simulation, s.planned = [], 0.0, None, []
    stops = list(s.stops)
    if s.start in stops or s.end in stops:
        s.message = 'Intermediate stops must differ from start and destination.'
        return
    requested = [s.start, *stops, s.end]
    if s.start == s.end and not stops:
        path, distance = [s.start], 0.0
    else:
        path, distance = navigator.calculate_route(requested, algorithm='auto')
    if not path:
        s.message = 'No route could be found.'
        return
    s.route, s.distance, s.planned = list(path), distance, requested
    s.simulation = CampusModel(s.route)
    s.floor = locations[path[0]]['floor']
    s.manual_floor = s.floor
    s.message = f'Route found: {len(path)-1} connections.' if len(path)>1 else 'You are already at your destination.'

def start():
    if s.simulation and s.simulation.student.current_step < len(s.route)-1:
        s.running = True
        s.next_tick = time.monotonic() + 1
        s.message = 'Simulation running.'

def pause():
    s.running = False
    s.message = "Simulation paused."


def reset():
    s.running = False
    if s.route:
        s.simulation = CampusModel(s.route)
        sync_floor()
        s.message = "Simulation reset."


def advance():
    if s.simulation is None:
        return

    s.simulation.step()
    node = current_node()
    sync_floor()

    if s.simulation.student.current_step >= len(s.route) - 1:
        s.running = False
        s.message = f"Destination reached: {locations[node]['name']}."
    else:
        s.message = f"Student is now at {locations[node]['name']}."


def create_map():
    floor = s.floor

    visible = [
        n for n in ids
        if locations[n]["floor"] == floor
    ]

    visible_set = set(visible)
    fig = go.Figure()

    def lines(pairs, color, width, name=None):
        x, y = [], []

        for a, b in pairs:
            if a in visible_set and b in visible_set:
                x.extend([
                    locations[a]["x"],
                    locations[b]["x"],
                    None
                ])

                y.extend([
                    locations[a]["y"],
                    locations[b]["y"],
                    None
                ])

        if x:
            fig.add_trace(go.Scatter(
                x=x,
                y=y,
                mode="lines",
                line=dict(color=color, width=width),
                hoverinfo="skip",
                name=name,
                showlegend=bool(name)
            ))

    edges = {
        tuple(sorted((a, b)))
        for a, neighbors in graph.adjacency_list.items()
        for b, _ in neighbors
    }

    lines(edges, "#8297B8", 1.8)

    lines(
        zip(s.route, s.route[1:]),
        "#A38BFF",
        5,
        "Selected route"
    )

    fig.add_trace(go.Scatter(
        x=[locations[n]["x"] for n in visible],
        y=[locations[n]["y"] for n in visible],
        mode="markers+text",
        text=visible,
        textposition="top center",
        textfont=dict(color="#DCE6FA", size=11),
        customdata=[
            [
                locations[n]["name"],
                locations[n]["building"],
                locations[n]["floor"]
            ]
            for n in visible
        ],
        marker=dict(
            size=11,
            color="#B5C8E8",
            line=dict(width=2, color="#E2E8F0")
        ),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "ID: %{text}<br>"
            "Building: %{customdata[1]}<br>"
            "Floor: %{customdata[2]}"
            "<extra></extra>"
        ),
        name="Campus locations"
    ))

    def marker(node, color, name, symbol="circle"):
        if node in visible_set:
            location = locations[node]

            fig.add_trace(go.Scatter(
                x=[location["x"]],
                y=[location["y"]],
                mode="markers",
                name=name,
                marker=dict(
                    size=19,
                    color=color,
                    symbol=symbol,
                    line=dict(width=2, color="#E2E8F0")
                ),
                hovertext=label(node),
                hoverinfo="text"
            ))

    transitions = {
        a for a, b in edges
        if a in visible_set and b not in visible_set
    } | {
        b for a, b in edges
        if b in visible_set and a not in visible_set
    }

    for i, node in enumerate(sorted(transitions)):
        location = locations[node]

        fig.add_trace(go.Scatter(
            x=[location["x"]],
            y=[location["y"]],
            mode="markers",
            name="Floor connection",
            showlegend=i == 0,
            marker=dict(
                size=15,
                symbol="square-open",
                color="#60A5FA",
                line=dict(width=2)
            ),
            hovertext=label(node),
            hoverinfo="text"
        ))

    planned = s.planned or [s.start, *s.stops, s.end]

    marker(planned[0], "#16A34A", "Start")
    marker(planned[-1], "#DC2626", "Destination")

    for i, node in enumerate(planned[1:-1], 1):
        marker(node, "#38BDF8", f"Stop {i}")

    marker(
        current_node(),
        "#F59E0B",
        "Student",
        "diamond"
    )

    fig.update_layout(
        height=590,
        paper_bgcolor="#253149",
        plot_bgcolor="#2A3852",
        font=dict(color="#E2E8F0"),
        margin=dict(l=15, r=15, t=55, b=15),
        legend=dict(
            orientation="h",
            y=1.02,
            yanchor="bottom"
        ),
        xaxis=dict(
            visible=False,
            scaleanchor="y",
            scaleratio=1
        ),
        yaxis=dict(visible=False),
        dragmode="pan",
        uirevision=str(floor)
    )

    return fig


# ==============================
# STREAMLIT USER INTERFACE
# ==============================

st.title("◈ Campus Navigator")

st.caption(
    "Navigate your campus with confidence "
    "· A* routing · Mesa simulation"
)

with st.sidebar:

    st.header("Plan your journey")

    st.selectbox(
        "Starting location",
        ids,
        format_func=label,
        key="start"
    )

    st.selectbox(
        "Destination",
        ids,
        index=min(1, len(ids) - 1),
        format_func=label,
        key="end"
    )

    st.multiselect(
        "Intermediate stops (in selection order)",
        ids,
        format_func=label,
        key="stops"
    )

    st.button(
        "Find route",
        type="primary",
        on_click=calculate,
        use_container_width=True
    )


@st.fragment(run_every=1.0 if s.running else None)
def navigation_panel():

    if s.running and time.monotonic() >= s.next_tick:
        advance()
        s.next_tick = time.monotonic() + 1

        if not s.running:
            st.rerun()

    left, right = st.columns([1, 2.5], gap="large")

    with left:

        with st.container(border=True):

            st.subheader("Route details")
            st.write(s.message)

            if s.route:

                st.metric(
                    "Distance",
                    f"{s.distance:.2f} units"
                )

                st.caption(
                    f"{len(s.route) - 1} connections · A*"
                )

                with st.expander("Route waypoints"):
                    for node in s.route:
                        st.write(label(node))

        with st.container(border=True):

            st.subheader("Student simulation")

            step = (
                s.simulation.student.current_step
                if s.simulation else 0
            )

            total = max(0, len(s.route) - 1)

            st.progress(
                step / total if total else float(bool(s.route)),
                text=f"{step} / {total} connections"
            )

            node = current_node()

            if node is not None:
                st.write(f"**Current:** {label(node)}")
                st.caption(
                    floor_label(locations[node]["floor"])
                )

            a, b = st.columns(2)

            if a.button(
                "Pause" if s.running else "Start / Resume",
                disabled=not s.route or step >= total,
                type="primary"
            ):
                pause() if s.running else start()
                st.rerun()

            if b.button("Reset", disabled=not s.route):
                reset()
                st.rerun()

    with right:

        with st.container(border=True):

            st.subheader("Interactive campus map")

            st.checkbox(
                "Automatically follow student floor",
                key="follow",
                on_change=sync_floor
            )

            if s.follow and current_node() is not None:

                st.caption(
                    f"Following student · {floor_label(s.floor)}"
                )

            else:

                s.floor = st.radio(
                    "Displayed floor",
                    floors,
                    index=floors.index(s.floor),
                    format_func=floor_label,
                    horizontal=True,
                    key="manual_floor"
                )

            st.plotly_chart(
                create_map(),
                use_container_width=True,
                theme=None,
                config={"scrollZoom": True},
                key="campus_map"
            )

            st.caption(
                f"{len(locations)} campus locations · "
                "Distances are illustrative, "
                "not surveyed walking measurements."
            )


navigation_panel()