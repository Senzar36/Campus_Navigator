import csv
import math


class CampusGraph:
    def __init__(self, locations_file, connections_file):
        self.locations = {}
        self.adjacency_list = {}

        self.load_locations(locations_file)
        self.load_connections(connections_file)

    def load_locations(self, file_path):
        with open(file_path, mode="r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                loc_id = row["location_id"].strip()
                floor = float(row["floor"])

                self.locations[loc_id] = {
                    "name": row["location_name"].strip(),
                    "building": row["building"].strip(),
                    "floor": floor,
                    "x": float(row["x"]),
                    "y": float(row["y"]),
                    "z": floor * 15.0,
                    "type": row["location_type"].strip(),
                }

                self.adjacency_list[loc_id] = []

    def load_connections(self, file_path):
        with open(file_path, mode="r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                loc1 = row["location_id_1"].strip()
                loc2 = row["location_id_2"].strip()

                if loc1 not in self.locations or loc2 not in self.locations:
                    raise ValueError(
                        f"Connection references an unknown location: {loc1}, {loc2}"
                    )

                distance = float(row["distance"])

                self.adjacency_list[loc1].append((loc2, distance))
                self.adjacency_list[loc2].append((loc1, distance))

    def calculate_distance(self, loc1_id, loc2_id):
        loc1 = self.locations[loc1_id]
        loc2 = self.locations[loc2_id]

        dx = loc1["x"] - loc2["x"]
        dy = loc1["y"] - loc2["y"]
        dz = loc1["z"] - loc2["z"]

        return math.sqrt(dx**2 + dy**2 + dz**2)


if __name__ == "__main__":
    import os

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    graph = CampusGraph(
        os.path.join(base_dir, "data", "Campus_Navigator_Dataset.csv"),
        os.path.join(base_dir, "data", "campus_connections.csv"),
    )

    print(f"Locations loaded: {len(graph.locations)}")
    print(f"Connections loaded: {sum(len(edges) for edges in graph.adjacency_list.values()) // 2}")

    for neighbor, distance in graph.adjacency_list["L001"]:
        print(f"Main Entrance -> {graph.locations[neighbor]['name']}: {distance:.2f} units")