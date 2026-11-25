
from __future__ import annotations

from graph import CampusGraph
from navigation import Navigator
from pathfinding import PathFinder


class TrackingPathFinder(PathFinder):
    

    def __init__(self, graph: CampusGraph):
        super().__init__(graph)
        self.segment_results = []
        self.selected_results = []

    def _save_result(self, algorithm, path, distance, explored, start_time):
        super()._save_result(algorithm, path, distance, explored, start_time)
        self.segment_results.append(dict(self.last_result))

    def auto_select(self, start_id, goal_id):
        path = super().auto_select(start_id, goal_id)
        self.selected_results.append(dict(self.last_result))
        return path


def find_route(graph: CampusGraph, start_id: str, destination_id: str,
               stops: list[str] | None = None, algorithm: str = "auto") -> dict:
    
    stops = list(stops or [])
    if algorithm not in {"auto", "astar", "gbfs"}:
        raise ValueError("Invalid routing algorithm.")
    if not start_id or not destination_id:
        raise ValueError("Select a starting location and a destination.")

    requested = [start_id, *stops, destination_id]
    if any(node not in graph.locations for node in requested):
        raise ValueError("One or more selected locations do not exist.")
    if start_id == destination_id and not stops:
        return {
            "path": [start_id], "distance": 0.0,
            "requested_stops": requested, "algorithm": algorithm,
            "nodes_explored": 0, "execution_time_ms": 0.0,
            "segment_results": [],
            "selected_results": [],
            "selected_algorithms": [],
        }
    if len(set(requested)) != len(requested):
        raise ValueError("Start, destination and intermediate stops must be different.")

    pf = TrackingPathFinder(graph)
    path, cost = Navigator(pf).calculate_route(requested, algorithm=algorithm)
    if not path:
        raise ValueError("No connected route was found for these locations.")
    selected_results = (
        pf.selected_results if algorithm == "auto"
        else pf.segment_results
    )

    return {
        "path": path,
        "distance": cost,
        "requested_stops": requested,
        "algorithm": algorithm,
        "nodes_explored": sum(m["nodes_explored"] for m in pf.segment_results),
        "execution_time_ms": sum(m["execution_time_ms"] for m in pf.segment_results),
        "segment_results": pf.segment_results,
        "selected_results": selected_results,
        "selected_algorithms": [
            m["algorithm"] for m in selected_results
        ],
    }


def compare_routes(graph: CampusGraph, start_id: str, destination_id: str,
                   stops: list[str] | None = None) -> list[dict]:
    
    results = []
    for algorithm, label in (("astar", "A* Search"), ("gbfs", "Greedy Best-First")):
        result = find_route(graph, start_id, destination_id, stops, algorithm)
        results.append({
            "Algorithm": label,
            "Distance (units)": round(result["distance"], 2),
            "Connections": max(len(result["path"]) - 1, 0),
            "Nodes explored¹": result["nodes_explored"],
            "Search time (ms)¹": round(result["execution_time_ms"], 4),
            "path": result["path"],
        })
    return results
