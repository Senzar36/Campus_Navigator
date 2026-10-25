class Navigator:
    def __init__(self, pathfinder):
        self.pathfinder = pathfinder
        self.graph = pathfinder.graph

    def calculate_route(self, stops, algorithm='astar'):
        if len(stops) < 2:
            return None, 0

        full_path = []
        total_cost = 0

        for i in range(len(stops) - 1):
            start_id = stops[i]
            goal_id = stops[i+1]
            
            if algorithm == 'astar':
                segment = self.pathfinder.a_star(start_id, goal_id)
            elif algorithm == 'gbfs':
                segment = self.pathfinder.greedy_best_first(start_id, goal_id)
            else:
                return None, 0
            
            if segment is None:
                return None, 0
            
            segment_cost = 0

            for j in range(len(segment) - 1):
                current_id = segment[j]
                next_id = segment[j + 1]

                for neighbor, weight in self.graph.adjacency_list[current_id]:
                    if neighbor == next_id:
                        segment_cost += weight
                        break
                else:
                    raise ValueError(
                        f"Invalid route: no connection between "
                        f"{current_id} and {next_id}"
                    )
              
            total_cost += segment_cost

            if i == 0:
                full_path.extend(segment)
            else:
                full_path.extend(segment[1:])

        return full_path, total_cost

if __name__ == "__main__":
    from graph import CampusGraph
    from pathfinding import PathFinder

    g = CampusGraph('data/Campus_Navigator_Dataset.csv', 'data/campus_connections.csv')
    pf = PathFinder(g)
    nav = Navigator(pf)
    
    route_stops = ['L001', 'L004', 'L005']
    
    path, cost = nav.calculate_route(route_stops, algorithm='astar')
    
    print(f"Required Stops: {route_stops}")
    print(f"Calculated Route: {path}")
    print(f"Total Route Cost: {cost:.2f}")