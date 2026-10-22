import csv
import math

locations = []
with open('data/Campus_Navigator_Dataset.csv', mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        row['floor'] = float(row['floor'])
        row['x'] = float(row['x'])
        row['y'] = float(row['y'])
        locations.append(row)

def calc_dist(loc1, loc2):
    z_diff = (loc1['floor'] - loc2['floor']) * 5
    return math.sqrt((loc1['x'] - loc2['x'])**2 + (loc1['y'] - loc2['y'])**2 + z_diff**2)

connections = set()

for i, loc1 in enumerate(locations):
    distances = []
    for j, loc2 in enumerate(locations):
        if i != j and loc1['building'] == loc2['building']:
            dist = calc_dist(loc1, loc2)
            distances.append((dist, loc2['location_id']))
    
    distances.sort(key=lambda item: item[0])
    
    for dist, loc2_id in distances[:2]:
        edge = tuple(sorted([loc1['location_id'], loc2_id]))
        connections.add(edge)

with open('data/campus_connections.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['location_id_1', 'location_id_2'])
    for edge in connections:
        writer.writerow([edge[0], edge[1]])

print(f"Generated {len(connections)} connections successfully!")