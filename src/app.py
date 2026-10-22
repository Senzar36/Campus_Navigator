import sys
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import CampusGraph
from pathfinding import PathFinder
from navigation import Navigator

app = FastAPI(title="Campus Navigator")

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")

try:
    g = CampusGraph(os.path.join(base_dir, 'data', 'Campus_Navigator_Dataset.csv'), 
                    os.path.join(base_dir, 'data', 'campus_connections.csv'))
    pf = PathFinder(g)
    nav = Navigator(pf)
except Exception as e:
    print(f"Error loading data: {e}")
    sys.exit(1)

class RouteRequest(BaseModel):
    start: str
    dest: str
    stops: str = ""

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/locations")
async def get_locations():
    return g.locations

@app.post("/calculate")
async def calculate(req: RouteRequest):
    start = req.start.strip().upper()
    dest = req.dest.strip().upper()
    
    if start not in g.locations or dest not in g.locations:
        return {"error": "Invalid start or destination location"}

    route_stops = [start]
    if req.stops and req.stops.strip().upper() in g.locations:
        route_stops.append(req.stops.strip().upper())
    route_stops.append(dest)

    path_astar, cost_astar = nav.calculate_route(route_stops, algorithm='astar')
    path_gbfs, cost_gbfs = nav.calculate_route(route_stops, algorithm='gbfs')

    if not path_astar and not path_gbfs:
        return {"error": "Route not found"}

    best_path = path_astar
    best_cost = cost_astar
    best_algo = "A* Search"

    if path_gbfs and (not path_astar or cost_gbfs < cost_astar):
        best_path = path_gbfs
        best_cost = cost_gbfs
        best_algo = "Greedy Best-First Search"

    detailed_path = []
    for loc_id in best_path:
        loc = g.locations[loc_id]
        detailed_path.append({
            'id': loc_id,
            'name': loc['name'],
            'building': loc['building'],
            'floor': loc['floor']
        })
    
    return {
        "path": detailed_path, 
        "cost": round(best_cost, 2), 
        "algorithm": best_algo
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)