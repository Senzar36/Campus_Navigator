import heapq

class PathFinder:
    def __init__(self, graph):
        self.graph = graph

    def heuristic(self, current_id, goal_id):
        return self.graph.calculate_distance(current_id, goal_id)

    def reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def a_star(self, start_id, goal_id):
        open_set = []
        heapq.heappush(open_set, (0, start_id))
        came_from = {}
        g_score = {loc: float('inf') for loc in self.graph.locations}
        g_score[start_id] = 0
        f_score = {loc: float('inf') for loc in self.graph.locations}
        f_score[start_id] = self.heuristic(start_id, goal_id)

        while open_set:
            current_f, current = heapq.heappop(open_set)

            if current == goal_id:
                return self.reconstruct_path(came_from, current)

            for neighbor, weight in self.graph.adjacency_list[current]:
                tentative_g_score = g_score[current] + weight
                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal_id)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return None

    def greedy_best_first(self, start_id, goal_id):
        open_set = []
        heapq.heappush(open_set, (0, start_id))
        came_from = {}
        visited = set()
        visited.add(start_id)

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal_id:
                return self.reconstruct_path(came_from, current)

            for neighbor, _ in self.graph.adjacency_list[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    came_from[neighbor] = current
                    priority = self.heuristic(neighbor, goal_id)
                    heapq.heappush(open_set, (priority, neighbor))
        
        return None

if __name__ == "__main__":
    from graph import CampusGraph
    g = CampusGraph('data/Campus_Navigator_Dataset.csv', 'data/campus_connections.csv')
    pf = PathFinder(g)
    
    start_node = 'L001'
    end_node = 'L005'
    
    path_astar = pf.a_star(start_node, end_node)
    print(f"A* Path from {start_node} to {end_node}: {path_astar}")
    
    path_gbfs = pf.greedy_best_first(start_node, end_node)
    print(f"GBFS Path from {start_node} to {end_node}: {path_gbfs}")