# Campus Navigator

## Overview
Campus Navigator is an academic project designed to calculate and display optimal walking routes between locations on a college campus. It represents the campus as a weighted graph, supporting multi-floor navigation and ordered intermediate stops.

## Features
* **Graph-Based Routing:** Uses a custom adjacency list to represent campus locations (vertices) and walkable paths (edges).
* **Multiple Algorithms:** Implements both A* (A-Star) Search and Greedy Best-First Search (GBFS).
* **Multi-Floor Support:** Calculates physical 3D distance by applying a traversal cost penalty for floor transitions.
* **Intermediate Stops:** Supports routing through one or multiple required locations in a specific sequence before reaching the final destination.
* **Command-Line Interface:** Provides a clean, argument-driven CLI for quick route generation.

## Project Architecture
* `data/`
  * `Campus_Navigator_Dataset.csv`: Core location metadata (ID, name, building, floor, coordinates).
  * `campus_connections.csv`: Edge list defining valid walkable paths between locations.
* `src/`
  * `generate_connections.py`: Utility script to bootstrap a baseline edge list based on building proximity.
  * `graph.py`: Parses CSV data and constructs the weighted adjacency list.
  * `pathfinding.py`: Contains the A* and GBFS algorithm implementations.
  * `navigation.py`: Orchestrates multi-stop route segments and calculates total cost.
  * `main.py`: The command-line interface entry point.
* `tests/`
  * `test_navigation.py`: Unit tests verifying routing logic and edge cases.

## Setup and Usage

### Prerequisites
* Python 3.x

### 1. View Available Locations
```bash
python src/main.py --list