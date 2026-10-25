import heapq
import time


class PathFinder:
    def __init__(self, graph):
        self.graph = graph
        self.last_result = {}

    def heuristic(self, current_id, goal_id):
        return self.graph.calculate_distance(current_id, goal_id)

    def reconstruct_path(self, came_from, current):
        path = [current]

        while current in came_from:
            current = came_from[current]
            path.append(current)

        path.reverse()
        return path

    def calculate_path_cost(self, path):
        total_cost = 0

        for current, next_node in zip(path, path[1:]):
            for neighbor, weight in self.graph.adjacency_list[current]:
                if neighbor == next_node:
                    total_cost += weight
                    break

        return total_cost

    def _validate_locations(self, start_id, goal_id):
        if start_id not in self.graph.locations:
            raise ValueError(f"Unknown starting location: {start_id}")

        if goal_id not in self.graph.locations:
            raise ValueError(f"Unknown destination: {goal_id}")

    def _save_result(self, algorithm, path, distance, explored, start_time):
        self.last_result = {
            "algorithm": algorithm,
            "path": path,
            "distance": distance,
            "nodes_explored": explored,
            "execution_time_ms": (time.perf_counter() - start_time) * 1000,
        }

    def a_star(self, start_id, goal_id):
        start_time = time.perf_counter()
        self._validate_locations(start_id, goal_id)

        came_from = {}
        g_score = {
            loc: float("inf") for loc in self.graph.locations
        }
        g_score[start_id] = 0

        open_set = [
            (self.heuristic(start_id, goal_id), 0, start_id)
        ]

        explored_nodes = set()

        while open_set:
            _, queued_g, current = heapq.heappop(open_set)

            # Ignore queue entries made outdated by a better route.
            if queued_g != g_score[current]:
                continue

            if current in explored_nodes:
                continue

            explored_nodes.add(current)

            if current == goal_id:
                path = self.reconstruct_path(came_from, current)

                self._save_result(
                    "A*",
                    path,
                    g_score[goal_id],
                    len(explored_nodes),
                    start_time,
                )

                return path

            for neighbor, weight in self.graph.adjacency_list[current]:
                tentative_g = g_score[current] + weight

                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g

                    priority = (
                        tentative_g
                        + self.heuristic(neighbor, goal_id)
                    )

                    heapq.heappush(
                        open_set,
                        (priority, tentative_g, neighbor),
                    )

        self._save_result(
            "A*", None, float("inf"), len(explored_nodes), start_time
        )

        return None

    def greedy_best_first(self, start_id, goal_id):
        start_time = time.perf_counter()
        self._validate_locations(start_id, goal_id)

        open_set = [
            (self.heuristic(start_id, goal_id), start_id)
        ]

        came_from = {}
        discovered = {start_id}
        explored_nodes = set()

        while open_set:
            _, current = heapq.heappop(open_set)

            if current in explored_nodes:
                continue

            explored_nodes.add(current)

            if current == goal_id:
                path = self.reconstruct_path(came_from, current)

                self._save_result(
                    "GBFS",
                    path,
                    self.calculate_path_cost(path),
                    len(explored_nodes),
                    start_time,
                )

                return path

            for neighbor, _ in self.graph.adjacency_list[current]:
                if neighbor not in discovered:
                    discovered.add(neighbor)
                    came_from[neighbor] = current

                    priority = self.heuristic(neighbor, goal_id)
                    heapq.heappush(
                        open_set,
                        (priority, neighbor),
                    )

        self._save_result(
            "GBFS", None, float("inf"), len(explored_nodes), start_time
        )

        return None


if __name__ == "__main__":
    import os
    from graph import CampusGraph

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    graph = CampusGraph(
        os.path.join(base_dir, "data", "Campus_Navigator_Dataset.csv"),
        os.path.join(base_dir, "data", "campus_connections.csv"),
    )

    pathfinder = PathFinder(graph)

    for search in (pathfinder.a_star, pathfinder.greedy_best_first):
        path = search("L001", "L005")
        result = pathfinder.last_result

        print(f"\nAlgorithm: {result['algorithm']}")
        print(f"Path: {path}")
        print(f"Distance: {result['distance']:.2f} units")
        print(f"Nodes expanded: {result['nodes_explored']}")
        print(f"Execution time: {result['execution_time_ms']:.4f} ms")