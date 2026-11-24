"""Campus Navigator / Field Guide edition.

A Streamlit user interface connected directly to the original campus graph,
A* / Greedy Best-First search, ordered-stop navigation, and Mesa simulation.

Run from the project root:
    python -m streamlit run src/streamlit_app.py
"""
from __future__ import annotations

import html
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app_logic import compare_routes, find_route
from campus_ui import create_map, route_rows
from graph import CampusGraph
from simulation import CampusModel

st.set_page_config(
    page_title="Campus Navigator — Field Guide",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# This is a completely new light, editorial / wayfinding design.
# Backend calculations live in app_logic.py + the original backend modules.
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
:root {
  --paper: #F6F4EE;
  --surface: #FFFEFA;
  --ink: #26352E;
  --forest: #285342;
  --terracotta: #AD5033;
  --muted: #727C72;
  --line: #DEDFD6;
  --soft: #F0EEE5;
}
html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--paper) !important;
  color: var(--ink) !important;
  font-family: 'IBM Plex Sans', 'Segoe UI', sans-serif !important;
}
[data-testid="stHeader"] {
  background: var(--paper) !important;
}
[data-testid="stToolbar"] { right: 14px; }
[data-testid="stMainBlockContainer"] {
  max-width: 1480px !important;
  padding-top: 4rem !important;
  padding-bottom: 3rem !important;
}
#MainMenu { visibility: hidden; }
.stApp h1, .stApp h2, .stApp h3 {
  color: var(--ink) !important;
  font-family: 'IBM Plex Sans', sans-serif;
  letter-spacing: -0.035em;
}
p, label, div[data-testid="stCaptionContainer"] { color: var(--ink); }
div[data-testid="stCaptionContainer"] p { color: var(--muted) !important; font-size: .82rem; }

/* The identity is deliberately more like a campus field guide than a SaaS app. */
.masthead {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; padding: 8px 0 16px;
  border-bottom: 1px solid #CACFC2;
}
.wordmark { display: flex; align-items:center; gap: 12px; }
.mark {
  display: grid; place-items:center;
  width: 37px; height: 37px;
  background: var(--forest); color: #FFFDF6;
  border-radius: 4px; font-size: 1.05rem; font-weight: 700;
  letter-spacing: -.04em;
}
.wordmark-main { font-size: 1rem; letter-spacing: -.02em; font-weight: 700; line-height: 1.2; }
.wordmark-sub, .masthead-right, .eyebrow, .section-kicker,
.map-index, .meta-line, .micro, .footer {
  font-family: 'IBM Plex Mono', 'Consolas', monospace;
  letter-spacing: .07em;
}
.wordmark-sub { color: var(--muted); font-size: .63rem; margin-top: 3px; }
.masthead-right { color: #6F7B6D; font-size: .65rem; text-align: right; }

.hero {
  display: flex; justify-content: space-between;
  align-items: stretch; gap: 25px;
  padding: 27px 0 23px;
}
.hero-main { flex: 1; max-width: 850px; }
.eyebrow { font-size: .67rem; font-weight: 600; color: var(--terracotta); }
.hero-title {
  font: normal clamp(2.25rem, 4vw, 3.75rem)/1.06 'DM Serif Display', Georgia, serif;
  color: var(--ink); margin: 10px 0 13px;
  letter-spacing: -.032em;
}
.hero-title em { color: var(--terracotta); font-weight: normal; }
.hero-subtitle { max-width: 700px; color: #657267; font-size: .98rem; line-height: 1.65; }
.hero-aside {
  min-width: 210px; padding: 14px 17px;
  background: #E8E9DC; border-left: 3px solid var(--forest);
  display: flex; flex-direction: column; justify-content: space-between;
}
.aside-top { font: 600 .62rem 'IBM Plex Mono',monospace; letter-spacing: .1em; color:#5E6C5F; }
.aside-symbol { font: normal 2.2rem Georgia,serif; color:#406B57; text-align:right; line-height:1.3; }
.aside-bottom { font-size:.8rem; font-weight:600; line-height:1.45; color:#395346; }

.section-kicker { color: var(--terracotta); font-size: .65rem; font-weight: 600; margin-top: 7px; }
.section-title { font-size: 1.48rem; font-weight: 650; line-height:1.2; margin: 6px 0 13px; letter-spacing:-.04em; }
.section-desc { color:#657267; font-size:.88rem; line-height:1.55; margin-bottom: 11px; }
.map-heading { display:flex; justify-content:space-between; align-items:baseline; gap:10px; }
.map-index { color:#7A8478; font-size:.61rem; }

/* Native Streamlit controls remain accessible and actually interactive. */
[data-testid="stForm"] {
  border: 1px solid var(--line) !important;
  border-radius: 7px !important;
  padding: 17px 17px 19px !important;
  background: var(--surface) !important;
}
[data-testid="stForm"] label p, .stSelectbox label p, .stSelectSlider label p {
  font-size:.82rem !important; font-weight:600 !important; color:#3D4B42 !important;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stSelectSlider"] { border-radius: 5px !important; }
.stButton > button, [data-testid="stFormSubmitButton"] button {
  border-radius: 5px !important;
  font-family: 'IBM Plex Sans',sans-serif !important;
  font-weight: 600 !important;
  border: 1px solid #CDD1C5 !important;
  background: var(--surface) !important;
  color: var(--forest) !important;
  min-height: 39px;
}
.stButton > button:hover, [data-testid="stFormSubmitButton"] button:hover {
  border-color: var(--terracotta) !important;
  color: var(--terracotta) !important;
}
.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] button[kind="primary"] {
  background: var(--forest) !important;
  border-color: var(--forest) !important;
  color: #FFFEFA !important;
}
.stButton > button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
  background: #1D4234 !important;
  color: #FFFFFF !important;
}
.stButton > button:disabled { opacity:.45; }
[data-testid="stPlotlyChart"] {
  border: 1px solid var(--line);
  border-radius: 6px; overflow: hidden;
  background: #FAF9F5;
}
[data-testid="stMetric"] {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 5px;
  padding: 12px 13px;
}
[data-testid="stMetricLabel"] p {
  font-size:.73rem !important; color:#738076 !important;
  font-family: 'IBM Plex Mono',monospace !important;
}
[data-testid="stMetricValue"] {
  color:var(--forest) !important;
  font-weight: 650 !important;
  font-size: 1.4rem !important;
}
[data-testid="stExpander"] {
  background: var(--surface) !important;
  border:1px solid var(--line) !important;
  border-radius:5px !important;
}
[data-testid="stExpander"] summary { color:var(--forest); font-weight:600; }
[data-testid="stProgressBar"] div[role="progressbar"] { background:var(--terracotta) !important; }
hr { border-color: var(--line) !important; }

.status-note {
  margin: 12px 0 17px; padding: 10px 13px;
  border-left: 3px solid #49725F;
  background: #EAF0E8; color:#365747;
  font-size:.82rem; font-weight:500; line-height:1.5;
}
.small-note { color:#778075; font-size:.8rem; line-height:1.6; margin:11px 0 0; }
.top-rule { border:0; border-top:1px solid var(--line); margin:20px 0 15px; }
.legend-note { display:flex;flex-wrap:wrap;gap:15px;color:#788073;font-size:.72rem;margin:4px 0 10px; }
.key-dot { display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px; }

.sim-bar {
  margin-top: 16px; margin-bottom: 12px; border-top:1px solid var(--line);
  padding-top: 16px;
}
.sim-title { font-weight:650; font-size:1.12rem; margin-bottom:4px; }
.sim-sub {color:#778075;font-size:.82rem;margin-bottom:12px;}
.route-nodes { display:flex; flex-wrap:wrap; gap:7px; margin:12px 0; }
.route-node {
  padding: 6px 9px; font:.7rem 'IBM Plex Mono',monospace;
  background: #E8E8E0; border:1px solid #D8DCD1;
  border-radius:3px;color:#5C695E;
}
.route-node.active { background:var(--terracotta);color:#FFFFFF;border-color:var(--terracotta);font-weight:600; }
.route-node.done {background:#DDE9DE;color:#38634B;border-color:#C3D2C3;}
.footer { margin-top: 34px; padding-top: 15px; border-top:1px solid var(--line); font-size:.66rem;color:#758176; }
@media (max-width: 800px) {
  .masthead-right, .hero-aside {display:none;}
  .hero {padding:24px 0 18px;}
  .hero-title {font-size:2.55rem;}
  .hero-subtitle {font-size:.89rem;}
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource(show_spinner="Reading campus locations…")
def get_graph():
    return CampusGraph(
        str(ROOT_DIR / "data" / "Campus_Navigator_Dataset.csv"),
        str(ROOT_DIR / "data" / "campus_connections.csv"),
    )


graph = get_graph()
location_ids = sorted(graph.locations)
num_paths = sum(len(neighbors) for neighbors in graph.adjacency_list.values()) // 2
floor_numbers = sorted({int(value["floor"]) for value in graph.locations.values()})


def location_label(node_id):
    if node_id is None:
        return "None — direct route"
    place = graph.locations[node_id]
    floor = "G" if int(place["floor"]) == 0 else str(int(place["floor"]))
    return f"{place['name']} · {place['building']} · F{floor} ({node_id})"


def initialize_state():
    default_destination = "L005" if "L005" in graph.locations else location_ids[min(1, len(location_ids) - 1)]
    defaults = {
        "start_id": location_ids[0],
        "destination_id": default_destination,
        "algo_choice": "astar",
        "stop_count": 0,
        "route_result": None,
        "simulation_model": None,
        "sim_running": False,
        "sim_last_tick": time.monotonic(),
        "sim_delay": 1.0,
        "status_message": "Choose locations and select Find route to begin.",
        "status_error": False,
        "comparison": None,
        "floor_view": "All floors",
        "show_labels": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_state()


def clear_result():
    state = st.session_state
    state["route_result"] = None
    state["simulation_model"] = None
    state["sim_running"] = False
    state["comparison"] = None
    state["status_message"] = "Route changed — select Find route to recalculate."
    state["status_error"] = False


def swap_locations():
    state = st.session_state
    state["start_id"], state["destination_id"] = state["destination_id"], state["start_id"]
    clear_result()


def add_stop():
    st.session_state["stop_count"] = min(st.session_state["stop_count"] + 1, 8)
    clear_result()


def remove_stop():
    state = st.session_state
    if state["stop_count"]:
        # Only the last stop is removed; previous selected stops retain their values.
        state.pop(f"stop_{state['stop_count'] - 1}", None)
        state["stop_count"] -= 1
        clear_result()


def process_route():
    state = st.session_state
    chosen_stops = [state.get(f"stop_{i}") for i in range(state["stop_count"])]
    chosen_stops = [node for node in chosen_stops if node is not None]
    state["sim_running"] = False
    state["comparison"] = None
    try:
        result = find_route(
            graph, state["start_id"], state["destination_id"],
            stops=chosen_stops, algorithm=state["algo_choice"],
        )
    except ValueError as error:
        state["route_result"] = None
        state["simulation_model"] = None
        state["status_message"] = str(error)
        state["status_error"] = True
        return
    state["route_result"] = result
    state["simulation_model"] = CampusModel(result["path"])
    state["sim_last_tick"] = time.monotonic()
    state["status_error"] = False
    state["status_message"] = (
        "You're already at your destination."
        if len(result["path"]) == 1
        else f"Route found — {len(result['path']) - 1} connected segments."
    )


def move_one_step():
    state = st.session_state
    model = state["simulation_model"]
    if model is None or model.finished:
        state["sim_running"] = False
        return
    model.step()
    state["sim_last_tick"] = time.monotonic()
    if model.finished:
        state["sim_running"] = False


def reset_simulation():
    state = st.session_state
    if state["route_result"] is not None:
        state["simulation_model"] = CampusModel(state["route_result"]["path"])
        state["sim_last_tick"] = time.monotonic()
        state["sim_running"] = False


# -------------------------------------------------------
# Identity / introduction
# -------------------------------------------------------
st.markdown("""
<div class="masthead">
  <div class="wordmark">
    <span class="mark">CN.</span>
    <div><div class="wordmark-main">Campus Navigator</div>
      <div class="wordmark-sub">THE UNIVERSITY WAYFINDING TOOL</div></div>
  </div>
  <div class="masthead-right">FUNDAMENTALS OF AI &nbsp; / &nbsp; CAMPUS GRAPH PROJECT</div>
</div>
<div class="hero">
  <div class="hero-main">
    <div class="eyebrow">A CAMPUS FIELD GUIDE &nbsp; • &nbsp; ISSUE 01 / ROUTES</div>
    <div class="hero-title">Know where you're going.<br><em>Enjoy getting there.</em></div>
    <div class="hero-subtitle">Plan a route between buildings, classrooms and campus spaces. Follow the path on a layered map, or watch a virtual student make the journey.</div>
  </div>
  <div class="hero-aside">
    <div class="aside-top">CAMPUS / WAYFINDING</div>
    <div class="aside-symbol">✣</div>
    <div class="aside-bottom">An interactive campus map built with graph search and agent simulation.</div>
  </div>
</div>
""", unsafe_allow_html=True)

planner, explorer = st.columns([0.92, 1.78], gap="large")

# -------------------------------------------------------
# Left column: journey inputs + project context
# -------------------------------------------------------
with planner:
    st.markdown("""
    <div class="section-kicker">01 / YOUR JOURNEY</div>
    <div class="section-title">Where are we heading?</div>
    <div class="section-desc">Pick two locations. Add stopovers in the order you want to visit them.</div>
    """, unsafe_allow_html=True)

    action_one, action_two = st.columns(2, gap="small")
    with action_one:
        st.button("⇅  Swap", on_click=swap_locations, key="swap_locations", use_container_width=True)
    with action_two:
        st.button("＋  Add stop", on_click=add_stop, key="add_stop",
                  use_container_width=True, disabled=st.session_state["stop_count"] >= 8)
    if st.session_state["stop_count"]:
        st.button("−  Remove last stop", on_click=remove_stop,
                  key="remove_stop", use_container_width=True)

    with st.form("journey_form", clear_on_submit=False):
        st.selectbox("Starting point", location_ids, format_func=location_label, key="start_id")
        for i in range(st.session_state["stop_count"]):
            st.selectbox(f"Stopover {i + 1}", [None, *location_ids],
                         format_func=location_label, key=f"stop_{i}")
        st.selectbox("Destination", location_ids, format_func=location_label,
                     key="destination_id")
        st.selectbox("Route method", ["astar", "gbfs"],
                     format_func=lambda algorithm: (
                         "A* — shortest weighted path" if algorithm == "astar"
                         else "Greedy Best-First — heuristic-based"
                     ), key="algo_choice")
        submitted = st.form_submit_button("Find route  →", type="primary",
                                          use_container_width=True)
    if submitted:
        process_route()

    if st.session_state["status_error"]:
        st.error(st.session_state["status_message"], icon="⚠️")
    else:
        st.markdown(
            "<div class='status-note'>" + html.escape(st.session_state["status_message"]) + "</div>",
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-kicker">THE CAMPUS IN NUMBERS</div>', unsafe_allow_html=True)
    count_one, count_two, count_three = st.columns(3, gap="small")
    count_one.metric("Points", len(graph.locations))
    count_two.metric("Links", num_paths)
    count_three.metric("Floors", len(floor_numbers))
    st.markdown("""
    <p class="small-note">This is a schematic campus graph, not GPS. The routing costs are dataset units, not surveyed walking metres.</p>
    <hr class="top-rule">
    """, unsafe_allow_html=True)
    with st.expander("How does the AI choose a route?"):
        st.markdown("""
The campus is represented as a **weighted graph**: locations are nodes and walkable paths are edges.

- **A-star** considers both distance already travelled and estimated remaining cost. The original backend uses a scaled 3D-distance heuristic.
- **Greedy Best-First Search** follows the estimated cost to the destination. It can find a longer route than A*.
- **Stopovers** are visited in the selected order, one search per leg.

The map is a visual layer. Calculations still come from the original Python backend.
""")


@st.fragment(run_every="1s")
def explorer_panel():
    """Refresh only the live map / simulation, rather than reloading the form."""
    state = st.session_state
    result = state["route_result"]
    model = state["simulation_model"]

    if state["sim_running"] and model is not None and not model.finished:
        if time.monotonic() - state["sim_last_tick"] >= state["sim_delay"]:
            move_one_step()
    if model is not None and model.finished:
        state["sim_running"] = False

    st.markdown("""
    <div class="section-kicker">02 / CAMPUS PLAN</div>
    <div class="map-heading">
      <div class="section-title">Explore the route</div>
      <span class="map-index">MAP / NOT TO SCALE</span>
    </div>
    """, unsafe_allow_html=True)

    floor_options = ["All floors", *[f"Floor {floor}" for floor in floor_numbers]]
    floor_column, toggle_column = st.columns([1.15, 0.85], gap="small")
    with floor_column:
        st.selectbox("Map level", floor_options, key="floor_view")
    with toggle_column:
        st.toggle("Show node codes", key="show_labels")

    path = result["path"] if result else []
    selected = result["requested_stops"] if result else [state["start_id"], state["destination_id"]]
    floor_filter = None if state["floor_view"] == "All floors" else int(state["floor_view"].split()[-1])
    agent_step = model.student.current_step if model else None
    figure = create_map(
        graph, path=path, current_step=agent_step,
        floor_filter=floor_filter,
        start_id=selected[0], destination_id=selected[-1],
        required_stops=selected[1:-1],
        show_labels=state["show_labels"],
    )
    st.plotly_chart(
        figure, use_container_width=True, theme=None,
        key="campus_graph_map",
        config={
            "displaylogo": False, "scrollZoom": True,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        },
    )
    st.markdown("""
    <div class="legend-note">
      <span><i class="key-dot" style="background:#2E6855"></i>Start</span>
      <span><i class="key-dot" style="background:#A94232"></i>Destination</span>
      <span><i class="key-dot" style="background:#B65C3A"></i>Route</span>
      <span><i class="key-dot" style="background:#E5A12A"></i>Student</span>
    </div>
    """, unsafe_allow_html=True)
    if floor_filter is None:
        st.caption("Each floor has its own panel to prevent overlapping rooms. Dashed lines mark floor changes. Drag to pan or scroll to zoom.")
    else:
        st.caption("This filter changes only the map display; route calculations still include all floors.")

    st.markdown('<hr class="top-rule"><div class="section-kicker">03 / ROUTE DETAILS</div>',
                unsafe_allow_html=True)
    if result is None:
        st.info("Select your journey and press Find route. Distance, directions and student simulation will appear here.",
                icon="📍")
        return

    total_steps = max(len(path) - 1, 0)
    current_step = model.student.current_step
    progress = 100 if total_steps == 0 else round(current_step / total_steps * 100)
    stat_columns = st.columns(4, gap="small")
    stat_columns[0].metric("Cost · units", f"{result['distance']:.2f}")
    stat_columns[1].metric("Connections", total_steps)
    stat_columns[2].metric("Method", "A*" if result["algorithm"] == "astar" else "GBFS")
    stat_columns[3].metric("Completed", f"{progress}%")

    st.markdown("""
    <div class="sim-bar">
      <div class="sim-title">Student movement</div>
      <div class="sim-sub">Follow an agent moving through the calculated path, one location at a time.</div>
    </div>
    """, unsafe_allow_html=True)
    start_button, pause_button, next_button, reset_button = st.columns(4, gap="small")
    with start_button:
        if st.button("▶  Start", type="primary", key="sim_start",
                     disabled=model.finished or state["sim_running"], use_container_width=True):
            state["sim_running"] = True
            state["sim_last_tick"] = time.monotonic()
            st.rerun(scope="fragment")
    with pause_button:
        if st.button("Ⅱ  Pause", key="sim_pause", disabled=not state["sim_running"],
                     use_container_width=True):
            state["sim_running"] = False
            st.rerun(scope="fragment")
    with next_button:
        if st.button("⏭  Step", key="sim_step", use_container_width=True,
                     disabled=model.finished or state["sim_running"]):
            move_one_step()
            st.rerun(scope="fragment")
    with reset_button:
        if st.button("↺  Reset", key="sim_reset", use_container_width=True):
            reset_simulation()
            st.rerun(scope="fragment")

    state["sim_delay"] = st.select_slider(
        "Seconds per connection", options=[1.0, 2.0, 3.0],
        value=state["sim_delay"],
        format_func=lambda value: f"{int(value)} sec",
        key="movement_speed_control",
    )
    st.progress(progress / 100)
    current = graph.locations[model.current_location_id]
    movement_state = (
        "Arrived" if model.finished else
        "In motion" if state["sim_running"] else "Paused / ready"
    )
    st.caption(
        f"{movement_state} · Point {current_step + 1} of {len(path)} · "
        f"Current location: **{current['name']}**, Floor {int(current['floor'])}"
    )

    node_tags = []
    for index, node in enumerate(path):
        class_name = " active" if index == current_step else " done" if index < current_step else ""
        node_tags.append(f'<span class="route-node{class_name}">{html.escape(node)}</span>')
    st.markdown('<div class="route-nodes">' + ''.join(node_tags) + '</div>',
                unsafe_allow_html=True)

    with st.expander("Turn-by-turn locations"):
        st.dataframe(pd.DataFrame(route_rows(graph, path, current_step)),
                     use_container_width=True, hide_index=True)
        floor_changes = sum(
            int(graph.locations[a]["floor"]) != int(graph.locations[b]["floor"])
            for a, b in zip(path, path[1:])
        )
        st.caption(f"Floor changes: {floor_changes}. All travel costs use the campus dataset's weighted connections.")
        if len(selected) > 2:
            st.caption("Visit order: " + " → ".join(selected))

    with st.expander("Compare A* and Greedy Best-First"):
        if st.button("Run comparison", key="compare_algorithms", use_container_width=True):
            state["comparison"] = compare_routes(
                graph, selected[0], selected[-1], selected[1:-1]
            )
        if state["comparison"]:
            table_data = [{key: value for key, value in item.items() if key != "path"}
                          for item in state["comparison"]]
            st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
            st.caption("Execution times and expanded-node counts are totals across the search legs. They reflect one run, not a benchmark. A* finds a minimum-cost route; Greedy Best-First may not.")
            for item in state["comparison"]:
                st.caption(f"{item['Algorithm']}: " + " → ".join(item["path"]))


with explorer:
    explorer_panel()

st.markdown("""
<div class="footer">CAMPUS NAVIGATOR / FIELD GUIDE EDITION &nbsp; · &nbsp; AI GRAPH SEARCH + MESA SIMULATION &nbsp; · &nbsp; ACADEMIC CAMPUS SCHEMATIC, NOT LIVE GPS</div>
""", unsafe_allow_html=True)
