import csv
import math

class CampusGraph:
    def __init__(self, locations_file, connections_file):
        self.locations = {}
        self.adjacency_list = {}
        self.load_locations(locations_file)
        self.load_connections(connections_file)

    def load_locations(self, file_path):
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                loc_id = row['location_id']
                self.locations[loc_id] = {
                    'name': row['location_name'],
                    'building': row['building'],
                    'floor': float(row['floor']),
                    'x': float(row['x']),
                    'y': float(row['y']),
                    'type': row['location_type']
                }
                self.adjacency_list[loc_id] = []

    def load_connections(self, file_path):
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                loc1 = row['location_id_1']
                loc2 = row['location_id_2']
                
                if loc1 in self.locations and loc2 in self.locations:
                    dist = self.calculate_distance(loc1, loc2)
                    self.adjacency_list[loc1].append((loc2, dist))
                    self.adjacency_list[loc2].append((loc1, dist))

    def calculate_distance(self, loc1_id, loc2_id):
        loc1 = self.locations[loc1_id]
        loc2 = self.locations[loc2_id]
        z_diff = (loc1['floor'] - loc2['floor']) * 5
        return math.sqrt((loc1['x'] - loc2['x'])**2 + (loc1['y'] - loc2['y'])**2 + z_diff**2)

if __name__ == "__main__":
    graph = CampusGraph('data/Campus_Navigator_Dataset.csv', 'data/campus_connections.csv')
    print(f"Graph built with {len(graph.locations)} locations.")
    
    first_loc = list(graph.locations.keys())[0]
    print(f"Connections for {first_loc}: {graph.adjacency_list[first_loc]}")