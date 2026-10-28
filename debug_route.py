import asyncio
import os
import sys

import mesa
import networkx as nx
import plotly.graph_objects as go
import solara

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import CampusGraph
from pathfinding import PathFinder
from navigation import Navigator

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

graph = CampusGraph(
    os.path.join(BASE_DIR, "data", "Campus_Navigator_Dataset.csv"),
    os.path.join(BASE_DIR, "data", "campus_connections.csv"),
)

pathfinder = PathFinder(graph)
navigator = Navigator(pathfinder)

campus_network = nx.Graph()

for location_id, location in graph.locations.items():
    campus_network.add_node(
        location_id,
        name=location["name"],
        x=location["x"],
        y=location["y"],
    )

for location_id, edges in graph.adjacency_list.items():
    for neighbor, distance in edges:
        campus_network.add_edge(
            location_id,
            neighbor,
            weight=distance,
        )

class StudentAgent(mesa.Agent):
    def __init__(self, model, path):
        super().__init__(model)
        self.path = path
        self.current_step = 0

    def step(self):
        if self.current_step < len(self.path) - 1:
            self.current_step += 1

class CampusModel(mesa.Model):
    def __init__(self, path):
        super().__init__()
        self.student = StudentAgent(self, path)

    def step(self):
        self.student.step()

location_labels = {
    f"{location['name']} ({location_id})": location_id
    for location_id, location in graph.locations.items()
}

location_options = list(location_labels.keys())

start_location = solara.reactive(
    location_options[0] if location_options else ""
)

destination = solara.reactive(
    location_options[1] if len(location_options) > 1 else ""
)

intermediate_stops = solara.reactive([""])

route = solara.reactive([])
route_distance = solara.reactive(0.0)
simulation = solara.reactive(None)
simulation_running = solara.reactive(False)

message = solara.reactive(
    "Choose your starting location and destination."
)


def create_campus_map():
    figure = go.Figure()

    # Draw all valid campus connections.
    for location_id, neighbor in campus_network.edges():
        first = graph.locations[location_id]
        second = graph.locations[neighbor]

        figure.add_trace(
            go.Scatter(
                x=[first["x"], second["x"]],
                y=[first["y"], second["y"]],
                mode="lines",
                line=dict(
                    color="#8297B8",
                    width=1.8,
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    if route.value:
        route_x = [
            graph.locations[node]["x"]
            for node in route.value
        ]

        route_y = [
            graph.locations[node]["y"]
            for node in route.value
        ]

        figure.add_trace(
            go.Scatter(
                x=route_x,
                y=route_y,
                mode="lines",
                line=dict(
                    color="#A38BFF",
                    width=5,
                ),
                name="Selected route",
                hoverinfo="skip",
            )
        )

    location_ids = list(graph.locations.keys())

    figure.add_trace(
        go.Scatter(
            x=[
                graph.locations[node]["x"]
                for node in location_ids
            ],
            y=[
                graph.locations[node]["y"]
                for node in location_ids
            ],
            mode="markers+text",
            text=location_ids,
            textfont=dict(color="#DCE6FA", size=11),
            textposition="top center",
            customdata=[
                [
                    graph.locations[node]["name"],
                    graph.locations[node]["building"],
                    graph.locations[node]["floor"],
                ]
                for node in location_ids
            ],
            marker=dict(
                size=11,
                color="#B5C8E8",
                line=dict(
                    width=2,
                    color="#E2E8F0",
                ),
            ),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "ID: %{text}<br>"
                "Building: %{customdata[1]}<br>"
                "Floor: %{customdata[2]}"
                "<extra></extra>"
            ),
            name="Campus locations",
        )
    )

    selected_locations = [
        (
            start_location.value,
            "#16A34A",
            "Start",
        ),
        (
            destination.value,
            "#DC2626",
            "Destination",
        ),
    ]

    for selected_label, color, label in selected_locations:
        selected_id = location_labels.get(selected_label)

        if selected_id in graph.locations:
            selected = graph.locations[selected_id]

            figure.add_trace(
                go.Scatter(
                    x=[selected["x"]],
                    y=[selected["y"]],
                    mode="markers",
                    marker=dict(
                        size=18,
                        color=color,
                        line=dict(
                            width=3,
                            color="#E2E8F0",
                        ),
                    ),
                    name=label,
                    hovertemplate=(
                        f"<b>{label}: "
                        f"{selected['name']}</b>"
                        "<extra></extra>"
                    ),
                )
            )

    if simulation.value is not None:
        agent = simulation.value.student

        agent_id = agent.path[agent.current_step]
        agent_location = graph.locations[agent_id]

        figure.add_trace(
            go.Scatter(
                x=[agent_location["x"]],
                y=[agent_location["y"]],
                mode="markers",
                marker=dict(
                    size=19,
                    color="#F59E0B",
                    symbol="diamond",
                    line=dict(
                        width=2,
                        color="#E2E8F0",
                    ),
                ),
                name="Student agent",
                hovertemplate=(
                    "<b>Student agent</b><br>"
                    f"{agent_location['name']}"
                    "<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        height=590,
        autosize=True,
        font=dict(color="#E2E8F0", family="Segoe UI, sans-serif"),
        hoverlabel=dict(bgcolor="#26334B", font_color="#F8FAFC"),
        margin=dict(
            l=12,
            r=12,
            t=58,
            b=12,
        ),
        paper_bgcolor="#253149",
        plot_bgcolor="#2A3852",
        showlegend=True,
        legend=dict(
            font=dict(color="#E2E8F0", size=12),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        xaxis=dict(
            visible=False,
            scaleanchor="y",
            scaleratio=1,
        ),
        yaxis=dict(
            visible=False,
        ),
        dragmode="pan",
    )

    return figure


def calculate_route():
    start_id = location_labels.get(start_location.value)

    destination_id = location_labels.get(
        destination.value
    )

    # Preserve the order selected by the user; empty optional rows are ignored.
    stop_ids = [location_labels.get(label) for label in intermediate_stops.value if label]

    if not start_id or not destination_id:
        message.value = (
            "Please select a valid starting point "
            "and destination."
        )
        return

    if any(stop_id is None for stop_id in stop_ids):
        message.value = "Please select valid intermediate stops."
        return

    selected_ids = [start_id, *stop_ids, destination_id]
    if len(selected_ids) != len(set(selected_ids)):
        message.value = "Start, destination and intermediate stops must all be different."
        return

    if start_id == destination_id and not stop_ids:
        route.value = [start_id]
        route_distance.value = 0.0
        simulation.value = CampusModel(route.value)
        simulation_running.value = False

        message.value = (
            "You are already at your destination."
        )
        return

    requested_stops = [start_id, *stop_ids, destination_id]

    calculated_path, distance = navigator.calculate_route(
        requested_stops,
        algorithm="astar",
    )

    if not calculated_path:
        route.value = []
        route_distance.value = 0.0
        simulation.value = None
        simulation_running.value = False

        message.value = (
            "No route could be found between "
            "the selected locations."
        )
        return

    route.value = calculated_path
    route_distance.value = distance
    simulation.value = CampusModel(calculated_path)
    simulation_running.value = False

    message.value = (
        f"Route found: {len(calculated_path) - 1} connections."
    )


def reset_simulation():
    if route.value:
        simulation.value = CampusModel(route.value)

    simulation_running.value = False
    message.value = "Simulation reset."


def advance_simulation():
    if simulation.value is None:
        message.value = (
            "Calculate a route before starting "
            "the simulation."
        )
        return

    agent = simulation.value.student

    if agent.current_step >= len(agent.path) - 1:
        simulation_running.value = False
        message.value = (
            "The student has reached the destination."
        )
        return

    simulation.value.step()

    agent_id = agent.path[agent.current_step]
    agent_location = graph.locations[agent_id]

    message.value = (
        f"Student is now at {agent_location['name']}."
    )

    if agent.current_step >= len(agent.path) - 1:
        message.value = (
            f"Destination reached: {agent_location['name']}."
        )

@solara.component
def Page():
    solara.Style("""
    :root { color-scheme: dark; }
    html, body, #app, #app > div, .v-application, .v-application--wrap,
    .v-main, .v-main__wrap, main, .solara-page, .solara-content,
    .solara-main, .solara-container, .container, .container-fluid {
        background-color: #151D2E !important;
    }
    .campus-root .v-sheet, .campus-root .v-card,
    .campus-root .theme--light.v-card {
        background-color: #253149 !important; color: #EAF0FC !important;
    }
    .campus-root .v-card__text, .campus-root .v-card__title,
    .campus-root .v-card p, .campus-root .v-card strong {
        color: #EAF0FC !important;
    }
    .campus-root .v-card .v-input__slot, .campus-root .v-card .v-field {
        background-color: #344460 !important;
    }
    .campus-root .v-card .v-btn:not(.primary) {
        background: #354664 !important; color: #EDF3FF !important;
    }
    .campus-root .v-btn.primary { background: #7165D9 !important; }
    .campus-root .v-card__title { letter-spacing: .01em !important; }
    .campus-root .v-card__text { line-height: 1.55 !important; }
    .campus-root .v-card { overflow: hidden; }
    .v-menu__content .v-list, .v-menu__content .v-list-item {
        background-color: #344460 !important; color: #F3F6FF !important;
    }

    html, body, #app, .v-application, .v-main, .v-main__wrap,
    .solara-page, .solara-content { background: #151D2E !important; }
    body { margin: 0 !important; }
    .v-application { color: #EAF0FC !important; }
    .campus-root, .campus-root > div { color: #EAF0FC !important; }
    .campus-root .v-card {
        background: #253149 !important; color: #EAF0FC !important;
        border: 1px solid #3A4A65 !important; border-radius: 16px !important;
        box-shadow: 0 8px 26px rgba(5, 12, 25, .15) !important;
    }
    .campus-root .v-card__title {
        color: #F5F7FF !important; font-size: 17px !important;
        font-weight: 650 !important; white-space: normal !important;
        overflow-wrap: anywhere !important;
    }
    .campus-root .v-card p, .campus-root .v-card strong,
    .campus-root .v-card label, .campus-root .v-card .v-label,
    .campus-root .v-card .v-input, .campus-root .v-card input,
    .campus-root .v-card .v-select__selection,
    .campus-root .v-card .v-select__selection-text,
    .campus-root .v-card .v-icon { color: #EAF0FC !important; }
    .campus-root .v-card .v-input__slot,
    .campus-root .v-card .v-field {
        background: #32425F !important; border-radius: 9px !important;
    }
    .campus-root .v-card .v-input__slot:before { border-color: #7789A5 !important; }
    .v-menu__content, .v-list, .v-list-item {
        background: #32425F !important; color: #F3F6FF !important;
    }
    .v-list-item__title { color: #F3F6FF !important; }
    .campus-root .v-btn {
        text-transform: none !important; letter-spacing: 0 !important;
        font-weight: 600 !important; border-radius: 9px !important;
    }
    .campus-root .v-btn.primary { background: #6679E8 !important; }
    .campus-root .js-plotly-plot, .campus-root .plot-container {
        max-width: 100% !important;
    }
    .campus-root .v-card__text { color: #EAF0FC !important; }
    .campus-root .v-card__text .markdown, .campus-root .v-card__text .prose {
        color: #EAF0FC !important;
    }
    /* Consistent typography for Solara Markdown and Vuetify widgets. */
    .campus-root .v-card .vue-markdown,
    .campus-root .v-card .vue-markdown *,
    .campus-root .v-card .solara-markdown,
    .campus-root .v-card .solara-markdown *,
    .campus-root .v-card .markdown,
    .campus-root .v-card .markdown *,
    .campus-root .v-card .prose,
    .campus-root .v-card .prose *,
    .campus-root .v-card .v-card__text p,
    .campus-root .v-card .v-card__text span:not(.v-btn__content),
    .campus-root .v-card .v-card__text li {
        color: #E8EFFB !important;
    }
    .campus-root .v-card .v-card__title,
    .campus-root .v-card h1,
    .campus-root .v-card h2,
    .campus-root .v-card h3,
    .campus-root .v-card strong {
        color: #FFFFFF !important;
    }
    .campus-root .v-input .v-label,
    .campus-root .v-input__details,
    .campus-root .v-messages,
    .campus-root .v-text-field__details {
        color: #C4D0E6 !important;
    }
    .campus-root .v-select__selection,
    .campus-root .v-select__selection-text,
    .campus-root .v-input input,
    .campus-root .v-field__input {
        color: #F7F9FF !important;
        -webkit-text-fill-color: #F7F9FF !important;
    }
    .campus-root .v-btn .v-btn__content { color: #FFFFFF !important; }
    .v-menu__content .v-list-item__title,
    .v-menu__content .v-list-item__content { color: #F7F9FF !important; }
    """)

    async def automatic_movement():
        while simulation_running.value:
            await asyncio.sleep(1)
            if not simulation_running.value:
                break
            advance_simulation()
            if simulation.value is None:
                simulation_running.value = False
                break
            agent = simulation.value.student
            if agent.current_step >= len(agent.path) - 1:
                simulation_running.value = False
                break

    movement_task = solara.lab.use_task(automatic_movement, dependencies=None)

    def start_movement():
        if simulation.value is None:
            message.value = "Calculate a route before starting."
            return
        agent = simulation.value.student
        if agent.current_step >= len(agent.path) - 1:
            message.value = "Reset the simulation to run again."
            return
        simulation_running.value = True
        movement_task()

    def pause_movement():
        simulation_running.value = False
        movement_task.cancel()
        message.value = "Simulation paused."

    def reset_movement():
        simulation_running.value = False
        movement_task.cancel()
        reset_simulation()

    def update_stop(index, selected):
        updated = list(intermediate_stops.value)
        updated[index] = selected
        intermediate_stops.value = updated

    def add_stop():
        intermediate_stops.value = [*intermediate_stops.value, ""]

    def remove_stop(index):
        updated = list(intermediate_stops.value)
        updated.pop(index)
        intermediate_stops.value = updated

    steps = max(len(route.value) - 1, 0)
    current_step = simulation.value.student.current_step if simulation.value is not None else 0
    progress = round(current_step * 100 / steps) if steps else 0

    with solara.Column(classes=["campus-root"], style={
        "width": "100%", "maxWidth": "1600px", "margin": "0 auto",
        "padding": "28px 28px 48px", "boxSizing": "border-box",
        "minHeight": "100vh", "gap": "20px",
        "fontFamily": "Segoe UI, Inter, sans-serif",
        "background": "radial-gradient(circle at 80% 0%, #30315B 0%, transparent 35%), linear-gradient(145deg, #19263C, #151D2E 65%, #1B2440)",
    }):
        # A single header surface, rather than white header strips.
        with solara.Card(classes=["campus-header"]):
            with solara.Column(style={"gap": "2px", "padding": "4px 8px"}):
                solara.Markdown("## ◈ Campus Navigator")
                solara.Markdown("**Navigate your campus with confidence.**  ·  A* routing  ·  Mesa simulation")

        # Main map gets priority; controls remain comfortably wide.
        with solara.Row(style={
            "width": "100%", "gap": "20px", "alignItems": "flex-start",
            "flexWrap": "wrap", "background": "transparent",
        }):
            with solara.Column(style={
                "flex": "1 1 310px", "maxWidth": "390px",
                "minWidth": "280px", "gap": "18px",
                "background": "transparent",
            }):
                with solara.Card("Plan your journey"):
                    solara.Markdown("Select your starting point, destination and stops in the order you want to visit them.")
                    solara.Select(label="Starting location", value=start_location, values=location_options)
                    solara.Select(label="Destination", value=destination, values=location_options)
                    for index, stop in enumerate(intermediate_stops.value):
                        with solara.Row(style={"gap": "8px", "alignItems": "center"}):
                            solara.Select(
                                label=f"Intermediate stop {index + 1} (optional)",
                                value=stop,
                                values=[""] + location_options,
                                on_value=lambda selected, i=index: update_stop(i, selected),
                            )
                            solara.Button("Remove", on_click=lambda i=index: remove_stop(i))
                    solara.Button("+ Add another stop", on_click=add_stop)
                    solara.Button("Find route →", on_click=calculate_route, color="primary")

                with solara.Card("Route details"):
                    solara.Markdown(f"**Status:** {message.value}")
                    if route.value:
                        solara.Markdown(f"**Distance:** {route_distance.value:.2f} illustrative units")
                        solara.Markdown(f"**Connections:** {steps}")
                        solara.Markdown("**Waypoints**")
                        for index, node_id in enumerate(route.value):
                            node = graph.locations[node_id]
                            prefix = "●" if index in (0, len(route.value) - 1) else "→"
                            solara.Markdown(f"{prefix} **{node_id}** — {node['name']}")
                    else:
                        solara.Markdown("Your route will appear here after calculation.")

                with solara.Card("Student simulation"):
                    solara.Markdown(f"**Progress:** {current_step} / {steps} connections ({progress}%)")
                    if simulation.value is not None:
                        agent_id = simulation.value.student.path[current_step]
                        solara.Markdown(f"**Current:** {graph.locations[agent_id]['name']}")
                    with solara.Row(style={"gap": "8px", "flexWrap": "wrap",
                                           "background": "transparent"}):
                        if simulation_running.value:
                            solara.Button("Pause", on_click=pause_movement)
                        else:
                            solara.Button("Start / Resume", on_click=start_movement, color="primary")
                        solara.Button("Reset", on_click=reset_movement)

            with solara.Column(style={
                "flex": "3 1 650px", "minWidth": "320px",
                "gap": "16px", "background": "transparent",
            }):
                with solara.Card("Interactive campus map"):
                    solara.Markdown(
                        "Hover over locations for details. Drag to pan and scroll to zoom."
                    )
                    solara.FigurePlotly(create_campus_map())
                with solara.Card("About this map"):
                    solara.Markdown(
                        f"**{len(graph.locations)} locations** connected by campus paths. "
                        "Distances are illustrative, not surveyed walking measurements."
                    )
