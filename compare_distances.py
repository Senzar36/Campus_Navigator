import csv
import math

# Load location information.
with open("data/Campus_Navigator_Dataset.csv", encoding="utf-8-sig") as file:
    locations = {
        row["location_id"]: row
        for row in csv.DictReader(file)
    }

# Read connections and compare distances.
with open("data/campus_connections.csv", encoding="utf-8-sig") as file:
    connections = csv.DictReader(file)

    for connection in connections:
        start = locations[connection["location_id_1"]]
        end = locations[connection["location_id_2"]]

        dx = float(start["x"]) - float(end["x"])
        dy = float(start["y"]) - float(end["y"])
        dz = 15 * (float(start["floor"]) - float(end["floor"]))

        calculated_distance = math.sqrt(
            dx**2 + dy**2 + dz**2
        )
        csv_distance = float(connection["distance"])

        if abs(csv_distance - calculated_distance) > 0.01:
            print(
                f"{connection['location_id_1']} -> "
                f"{connection['location_id_2']}: "
                f"CSV = {csv_distance:.2f}, "
                f"Calculated = {calculated_distance:.2f}"
            )

print("Distance comparison complete.")