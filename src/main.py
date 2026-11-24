import sys
import argparse
from graph import CampusGraph
from pathfinding import PathFinder
from navigation import Navigator

def display_locations(graph):
    print("\n--- Available Locations ---")
    for loc_id, data in graph.locations.items():
        print(f"{loc_id}: {data['name']} ({data['building']}, Floor {data['floor']})")
    print("---------------------------\n")

def main():
    parser = argparse.ArgumentParser(description="Campus Navigator")
    parser.add_argument('--list', action='store_true', help="List all available locations")
    parser.add_argument('--start', type=str, help="Starting Location ID")
    parser.add_argument('--dest', type=str, help="Destination Location ID")
    parser.add_argument('--stops', type=str, help="Comma-separated intermediate Location IDs", default="")
    parser.add_argument('--algo', type=str, choices=['astar', 'gbfs'], default='astar', help="Pathfinding algorithm (astar or gbfs)")
    
    args = parser.parse_args()

    try:
        g = CampusGraph('data/Campus_Navigator_Dataset.csv', 'data/campus_connections.csv')
        pf = PathFinder(g)
        nav = Navigator(pf)
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

    print("\n=== CAMPUS NAVIGATOR ===")

    if args.list:
        display_locations(g)
        return

    if not args.start or not args.dest:
        print("Please provide both --start and --dest arguments, or use --list to see locations.")
        print("Example: python src/main.py --start L001 --dest L005")
        return

    start = args.start.upper()
    dest = args.dest.upper()
    
    if start not in g.locations:
        print("Invalid Starting Location!")
        return
        
    if dest not in g.locations:
        print("Invalid Destination Location!")
        return
        
    stops = [start]
    if args.stops:
        stops.extend([stop.strip().upper() for stop in args.stops.split(',') if stop.strip().upper() in g.locations])
    stops.append(dest)
    
    path, cost = nav.calculate_route(stops, algorithm=args.algo)
    
    if path:
        print("\n--- ROUTE FOUND ---")
        print(f"Algorithm Used: {'Greedy Best-First' if args.algo == 'gbfs' else 'A*'}")
        print(f"Total Distance: {cost:.2f} units")
        print("Directions:")
        for i, loc_id in enumerate(path):
            loc = g.locations[loc_id]
            step = f"{i+1}. {loc['name']} ({loc['building']}, Floor {loc['floor']})"
            if loc_id in stops:
                step += " [REQUIRED STOP]"
            print(step)
    else:
        print("\n--- ROUTE NOT FOUND ---")
        print("Could not find a valid path connecting these locations.")

if __name__ == "__main__":
    main()