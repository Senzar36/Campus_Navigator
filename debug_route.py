import os
import sys

# Allow Python to import modules from src/.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from graph import CampusGraph
from pathfinding import PathFinder
from navigation import Navigator

# Load the campus graph.
graph = CampusGraph(
    "data/Campus_Navigator_Dataset.csv",
    "data/campus_connections.csv",
)

pathfinder = PathFinder(graph)
navigator = Navigator(pathfinder)

# Selected locations:
# Start: Main Entrance (L001)
# Intermediate: Project Lab (L029)
# Destination: Sports Ground Gate (L032)
stops = ["L001", "L029", "L032"]

print("=" * 60)
print("CAMPUS NAVIGATOR ROUTE DIAGNOSTIC")
print("=" * 60)

total_path, total_cost = navigator.calculate_route(
    stops,
    algorithm="astar",
)

if total_path is None:
    print("No valid route could be calculated.")
    raise SystemExit(1)

# Display each required route segment independently.
for index in range(len(stops) - 1):
    start_id = stops[index]
    goal_id = stops[index + 1]

    segment = pathfinder.a_star(start_id, goal_id)

    print(
        f"\nSEGMENT {index + 1}: "
        f"{graph.locations[start_id]['name']} -> "
        f"{graph.locations[goal_id]['name']}"
    )

    if segment is None:
        print("No route found for this segment.")
        continue

    segment_cost = pathfinder.calculate_path_cost(segment)

    for location_id in segment:
        name = graph.locations[location_id]["name"]
        floor = graph.locations[location_id]["floor"]
        print(f"  {location_id}: {name} (Floor {floor:g})")

    print(f"Segment distance: {segment_cost:.2f}")

# Display the complete combined route.
print("\n" + "=" * 60)
print("COMPLETE ROUTE")
print("=" * 60)

for location_id in total_path:
    name = graph.locations[location_id]["name"]
    print(f"{location_id} -> {name}")

print(f"\nTotal distance: {total_cost:.2f}")
print(f"Number of locations visited: {len(total_path)}")

# Check that every consecutive pair is a valid graph connection.
valid_route = True

for current, following in zip(total_path, total_path[1:]):
    neighbours = {
        neighbour
        for neighbour, _ in graph.adjacency_list[current]
    }

    if following not in neighbours:
        print(f"INVALID CONNECTION: {current} -> {following}")
        valid_route = False

print(
    "Connection validation:",
    "PASS" if valid_route else "FAIL",
)