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

intermediate_stop = solara.reactive("")

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
                    color="#71809E",
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
                    color="#8BA4FF",
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
                color="#A9B6D0",
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
        height=620,
        margin=dict(
            l=20,
            r=20,
            t=50,
            b=20,
        ),
        paper_bgcolor="#20283B",
        plot_bgcolor="#2A3349",
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

    stop_id = (
        location_labels.get(intermediate_stop.value)
        if intermediate_stop.value
        else None
    )

    if not start_id or not destination_id:
        message.value = (
            "Please select a valid starting point "
            "and destination."
        )
        return

    if stop_id == start_id or stop_id == destination_id:
        message.value = (
            "The intermediate stop must differ from "
            "the starting point and destination."
        )
        return

    if start_id == destination_id and stop_id is None:
        route.value = [start_id]
        route_distance.value = 0.0
        simulation.value = CampusModel(route.value)
        simulation_running.value = False

        message.value = (
            "You are already at your destination."
        )
        return

    requested_stops = [start_id]

    if stop_id:
        requested_stops.append(stop_id)

    requested_stops.append(destination_id)

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
    solara.Style(
        """
        .v-card {
            background-color: #222B3F !important;
            color: #EEF2F8 !important;
            border: 1px solid #35415A !important;
            border-radius: 12px !important;
            box-shadow: 0 5px 18px rgba(0, 0, 0, 0.14) !important;
        }

        .v-card-title,
        .v-card-text,
        .v-card-subtitle,
        .prose,
        .markdown,
        label {
            color: #EEF2F8 !important;
        }

        .v-label,
        .v-field-label,
        .v-card-text .text-medium-emphasis {
            color: #B8C3D8 !important;
        }

        .v-field {
            color: #EEF2F8 !important;
        }

        .v-field__input,
        .v-select__selection-text,
        .v-select__selection {
            color: #EEF2F8 !important;
        }

        .v-field__outline {
            color: #596782 !important;
        }

        .v-btn {
            border-radius: 8px !important;
            letter-spacing: 0.02em !important;
        }

        body {
            background-color: #111827;
        }
        """
    )

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

    movement_task = solara.lab.use_task(
        automatic_movement,
        dependencies=None,
    )
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
    with solara.Column(
        style={
            "maxWidth": "1500px",
            "margin": "0 auto",
            "padding": "28px",
            "fontFamily": "Inter, Segoe UI, sans-serif",
            "background": (
                "radial-gradient(ellipse at top left, "
                "rgba(79, 70, 229, 0.12), transparent 45%), "
                "radial-gradient(ellipse at top right, "
                "rgba(124, 58, 237, 0.08), transparent 40%), "
                "#111827"
            ),
            "color": "#F1F5F9",
            "minHeight": "100vh",
            "boxSizing": "border-box",
        }
    ):
        solara.Markdown("# Campus Navigator")
        solara.Markdown(
            "Built using A* and Greedy best First Search algorithms for pathfinding, "
            "and the Mesa framework for simulating a student navigating the campus."
        )

        with solara.Row(
            style={
                "alignItems": "flex-start",
                "gap": "20px",
            }
        ):
            with solara.Column(
                style={
                    "width": "320px",
                    "minWidth": "280px",
                }
            ):
                with solara.Card("Plan your journey"):
                    solara.Select(
                        label="Starting location",
                        value=start_location,
                        values=location_options,
                    )

                    solara.Select(
                        label="Destination",
                        value=destination,
                        values=location_options,
                    )

                    solara.Select(
                        label="Intermediate stop (optional)",
                        value=intermediate_stop,
                        values=[""] + location_options,
                    )

                    solara.Button(
                        "Find route",
                        on_click=calculate_route,
                        color="primary",
                    )

                with solara.Card("Route information"):
                    solara.Markdown(
                        f"**Status:** {message.value}"
                    )

                    if route.value:
                        solara.Markdown(
                            f"**Total distance:** "
                            f"{route_distance.value:.2f} units"
                        )

                        solara.Markdown(
                            f"**Connections:** "
                            f"{len(route.value) - 1}"
                        )

                        solara.Markdown("**Route:**")

                        solara.Markdown(
                            " → ".join(route.value)
                        )

                    with solara.Card("Student simulation"):
                        if simulation_running.value:
                            solara.Button(
                                "Pause",
                                on_click=pause_movement,
                            )
                        else:
                            solara.Button(
                                "Start / Resume",
                                on_click=start_movement,
                                color="primary",
                            )

                        solara.Button(
                            "Reset simulation",
                            on_click=reset_movement,
                        )


                    if simulation.value is not None:
                        agent = simulation.value.student

                        solara.Markdown(
                            f"**Progress:** "
                            f"{agent.current_step} / "
                            f"{max(len(agent.path) - 1, 0)} connections"
                        )

            with solara.Column(
                style={
                    "flex": "1",
                    "minWidth": "0",
                }
            ):
                with solara.Card("Campus map"):
                    solara.FigurePlotly(
                        create_campus_map()
                    )