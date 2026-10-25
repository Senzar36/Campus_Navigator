import os
import sys
import solara
import mesa
import networkx as nx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graph import CampusGraph
from pathfinding import PathFinder
from navigation import Navigator

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
g = CampusGraph(os.path.join(base_dir, 'data', 'Campus_Navigator_Dataset.csv'), 
                os.path.join(base_dir, 'data', 'campus_connections.csv'))
pf = PathFinder(g)
nav = Navigator(pf)

class StudentAgent(mesa.Agent):
    def __init__(self, model, path):
        # In Mesa 3.0+, Agent.__init__ only takes the model instance
        super().__init__(model)
        self.path = path
        self.current_step = 0

    def step(self):
        if self.current_step < len(self.path) - 1:
            self.current_step += 1
            next_node = self.path[self.current_step]
            self.model.grid.move_agent(self, next_node)

class CampusModel(mesa.Model):
    def __init__(self, G_nx, path):
        super().__init__()
        self.grid = mesa.space.NetworkGrid(G_nx)
        
        # Initialize agent with just the model and path
        self.student = StudentAgent(self, path)
        
        if path:
            self.grid.place_agent(self.student, path[0])

    def step(self):
        self.student.step()

G_nx = nx.Graph()
for loc_id in g.locations:
    G_nx.add_node(loc_id)
for loc_id, edges in g.adjacency_list.items():
    for neighbor, weight in edges:
        G_nx.add_edge(loc_id, neighbor, weight=weight)

start_val = solara.reactive("")
stop_val = solara.reactive("")
dest_val = solara.reactive("")
route_summary = solara.reactive([])
simulation_steps = solara.reactive([])
agent_path_str = solara.reactive("")

locations_dict = {f"{data['name']} ({loc_id})": loc_id for loc_id, data in g.locations.items()}
loc_names = list(locations_dict.keys())

if loc_names:
    start_val.value = loc_names[0]
    dest_val.value = loc_names[1]

@solara.component
def Page():
    with solara.Column(style={"padding": "40px", "maxWidth": "800px", "margin": "0 auto", "fontFamily": "sans-serif"}):
        solara.Markdown("# Campus Navigator Simulation")
        solara.Markdown("Agent-based point-to-point routing using **Mesa** and **Solara**.")
        
        with solara.Card("Navigation Parameters"):
            solara.Select(label="Starting Location", value=start_val, values=loc_names)
            solara.Select(label="Intermediate Stop (Optional)", value=stop_val, values=[""] + loc_names)
            solara.Select(label="Destination", value=dest_val, values=loc_names)
            
            def run_simulation():
                s_id = locations_dict.get(start_val.value)
                d_id = locations_dict.get(dest_val.value)
                i_id = locations_dict.get(stop_val.value) if stop_val.value else None
                
                req_stops = [s_id]
                if i_id: req_stops.append(i_id)
                req_stops.append(d_id)
                
                path, cost = nav.calculate_route(req_stops, algorithm='astar')
                
                if not path:
                    route_summary.value = ["Error: Route not found."]
                    simulation_steps.value = []
                    return
                
                summary = []
                summary.append(f"**Start:** {g.locations[s_id]['name']} ({s_id})")
                if i_id: 
                    summary.append(f"**Stop:** {g.locations[i_id]['name']} ({i_id})")
                summary.append(f"**Destination:** {g.locations[d_id]['name']} ({d_id})")
                summary.append(f"**Total Distance:** {cost:.2f} units")
                route_summary.value = summary
                
                agent_path_str.value = " ➔ ".join([f"{loc}" for loc in path])
                
                model = CampusModel(G_nx, path)
                steps_log = [f"Step 0: Agent spawned at {g.locations[path[0]]['name']}"]
                
                for i in range(len(path) - 1):
                    model.step()
                    current_loc = model.student.path[model.student.current_step]
                    steps_log.append(f"Step {i+1}: Agent moved to {g.locations[current_loc]['name']} ({current_loc})")
                
                simulation_steps.value = steps_log

            solara.Button("Calculate & Simulate Agent", on_click=run_simulation, color="primary")

        if route_summary.value:
            with solara.Card("Point-to-Point Detail"):
                for line in route_summary.value:
                    solara.Markdown(line)
                    
            if simulation_steps.value:
                with solara.Card("Agent Simulation Log"):
                    solara.Markdown(f"**Path used by agent:** {agent_path_str.value}")
                    for log in simulation_steps.value:
                        solara.Text(log)