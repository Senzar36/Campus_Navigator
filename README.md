# Campus Navigator — Streamlit Edition

Streamlit frontend for the existing **Fundamentals of AI Campus Navigator** backend. The graph-loading, A* search, Greedy Best-First Search and Navigator multi-stop implementation are preserved from the supplied project.

## Windows / VS Code: start here

1. Extract this ZIP into a normal folder (for example `Documents\Campus_Navigator_Streamlit`).
2. Open the **extracted root folder** in VS Code: **File → Open Folder**.
3. Open **Terminal → New Terminal** in VS Code.
4. Create and activate a virtual environment (recommended):

   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, you can use `\.venv\Scripts\python.exe` explicitly for the commands below, or switch to Command Prompt and run `.venv\Scripts\activate.bat`.

5. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

6. Launch the website **from the root of the extracted project**:

   ```powershell
   python -m streamlit run src/streamlit_app.py
   ```

7. Open the `http://localhost:8501` address displayed in your terminal, if your browser does not open automatically.

**Do not run** `python src/streamlit_app.py`; Streamlit apps are started with `streamlit run` or `python -m streamlit run`.

## Included features

- Pick campus start and destination from the actual CSV dataset.
- Add up to 8 ordered optional intermediate stops.
- Choose between **A\*** and **Greedy Best-First Search**, using the original `Navigator` and `PathFinder` classes.
- Explore an interactive Plotly campus graph, zoom/pan and hover for location details.
- View one floor or a floor-separated view; dashed links highlight floor transitions.
- View total weighted cost, connection count, navigation nodes, and search information.
- Start, pause, advance, and reset a **Mesa** student-agent simulation.
- See a live agent marker that advances one graph node at a time.
- Compare A* and GBFS on the same requested stops.

## Project layout

```text
Campus_Navigator_Streamlit/
├── .streamlit/
│   └── config.toml               # Dark app theme
├── data/
│   ├── Campus_Navigator_Dataset.csv
│   └── campus_connections.csv
├── src/
│   ├── streamlit_app.py          # NEW: complete Streamlit UI
│   ├── campus_ui.py              # NEW: Plotly campus schematic
│   ├── app_logic.py              # NEW: UI ↔ existing backend adapter
│   ├── simulation.py             # NEW: Mesa agent, extracted from Solara
│   ├── graph.py                  # UNCHANGED backend
│   ├── pathfinding.py            # UNCHANGED backend
│   ├── navigation.py             # UNCHANGED backend
│   ├── main.py                   # Original CLI
│   ├── solara_app.py             # Archived original interface
│   ├── solara_app_backup.py      # Archived older original interface
│   └── [other original tools]
├── tests/
│   ├── test_navigation.py
│   ├── test_streamlit_integration.py
│   └── test_mesa_simulation.py
├── requirements.txt
└── README.md
```

The old Solara files are preserved for reference, but Solara is intentionally **not** installed by the new `requirements.txt`. To run the old interface again, install its original requirements separately.

## How the UI connects to the backend

```python
from graph import CampusGraph
from pathfinding import PathFinder
from navigation import Navigator

graph = CampusGraph("data/Campus_Navigator_Dataset.csv", "data/campus_connections.csv")
pathfinder = PathFinder(graph)
navigator = Navigator(pathfinder)

path, cost = navigator.calculate_route(["L001", "L004", "L028"], algorithm="astar")
```

The new UI calls this same backend through `app_logic.find_route`, then passes the resulting `path` into `CampusModel(path)` for its Mesa step animation and into `campus_ui.create_map(...)` for visualization.

## Test backend and UI integration

From the project root:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

The original `test_navigation.py` covers route cases. `test_streamlit_integration.py` covers UI integration functions and plot creation without running the web server. `test_mesa_simulation.py` exercises the real Mesa model after you install dependencies.

## Notes for your presentation

- This is an **academic schematic**, not a surveyed campus map. The graph weights represent illustrative travel costs, not GPS walking metres.
- The vertical coordinate penalty is represented inside the existing graph, and the map offsets floor panels only for visualization (it does not change any path weights).
- A* is used for shortest weighted cost; Greedy Best-First may find a longer path because it prioritizes heuristic proximity over accumulated cost.
- Automatic movement updates the Mesa student agent through Streamlit's timed `st.fragment` reruns, **not** through a blocking `while` loop.
- Streamlit's session state holds the selected route and agent model independently for each browser session.

## Optional map-only preview

Double-click `campus_map_preview.html` to inspect a sample interactive Plotly route without starting Streamlit. This file is only a **sample visualization**; the interactive planner and moving Mesa agent run in the Streamlit app.
