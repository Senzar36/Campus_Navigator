import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import CampusGraph
from pathfinding import PathFinder

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

graph = CampusGraph(
    os.path.join(BASE_DIR, "data", "Campus_Navigator_Dataset.csv"),
    os.path.join(BASE_DIR, "data", "campus_connections.csv"),
)

pathfinder = PathFinder(graph)

routes = [
    ("L001", "L005"),  # Main Entrance -> Auditorium
    ("L001", "L015"),  # Main Entrance -> Room 201
    ("L001", "L028"),  # Main Entrance -> AI Lab
    ("L034", "L031"),  # Parking Area -> Food Court
    ("L030", "L017"),  # Canteen -> Room 203
]

algorithms = [
    ("A*", pathfinder.a_star),
    ("GBFS", pathfinder.greedy_best_first),
]

REPEATS = 100


def benchmark(algorithm, start, destination):
    """Run an algorithm repeatedly and calculate its average execution time."""
    times = []

    for _ in range(REPEATS):
        start_time = time.perf_counter()
        algorithm(start, destination)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        times.append(elapsed_ms)

    result = pathfinder.last_result.copy()

    return {
        "path": result["path"],
        "distance": result["distance"],
        "nodes_explored": result["nodes_explored"],
        "average_time_ms": statistics.mean(times),
    }


print(f"Campus Navigator: Algorithm Benchmark ({REPEATS} runs per test)")
print("=" * 120)

for start, destination in routes:
    start_name = graph.locations[start]["name"]
    destination_name = graph.locations[destination]["name"]

    print(f"\n{start_name} -> {destination_name}")
    print("-" * 120)

    print(
        f"{'Algorithm':<12}"
        f"{'Distance':<16}"
        f"{'Nodes expanded':<20}"
        f"{'Average time (ms)':<22}"
        f"Route"
    )

    for name, algorithm in algorithms:
        result = benchmark(algorithm, start, destination)
        path = result["path"]

        route = " -> ".join(path) if path else "No route found"

        distance = result["distance"]
        distance_text = (
            f"{distance:.2f}"
            if distance != float("inf")
            else "Unreachable"
        )

        print(
            f"{name:<12}"
            f"{distance_text:<16}"
            f"{result['nodes_explored']:<20}"
            f"{result['average_time_ms']:<22.6f}"
            f"{route}"
        )