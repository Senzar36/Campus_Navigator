"""Backend/UI integration tests that run without Streamlit or Mesa installed."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app_logic import compare_routes, find_route
from campus_ui import create_map, route_rows
from graph import CampusGraph


class TestStreamlitIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = CampusGraph(str(ROOT / "data" / "Campus_Navigator_Dataset.csv"),
                                str(ROOT / "data" / "campus_connections.csv"))

    def test_astar_uses_the_existing_backend(self):
        result = find_route(self.graph, "L001", "L005", algorithm="astar")
        self.assertEqual(result["path"][0], "L001")
        self.assertEqual(result["path"][-1], "L005")
        self.assertGreater(result["distance"], 0)
        self.assertGreater(result["nodes_explored"], 0)

    def test_stops_preserve_visit_order(self):
        result = find_route(self.graph, "L001", "L028", ["L004", "L009"])
        path = result["path"]
        self.assertLess(path.index("L004"), path.index("L009"))
        self.assertLess(path.index("L009"), path.index("L028"))
        self.assertEqual(len(result["segment_results"]), 3)

    def test_invalid_duplicate_selection(self):
        with self.assertRaisesRegex(ValueError, "different"):
            find_route(self.graph, "L001", "L005", ["L005"])

    def test_same_start_destination(self):
        result = find_route(self.graph, "L001", "L001")
        self.assertEqual(result["path"], ["L001"])
        self.assertEqual(result["distance"], 0)

    def test_both_algorithms(self):
        rows = compare_routes(self.graph, "L001", "L028")
        self.assertEqual(len(rows), 2)
        self.assertLessEqual(rows[0]["Distance (units)"], rows[1]["Distance (units)"])

    def test_plotly_map_all_floors_and_floor_filter(self):
        result = find_route(self.graph, "L001", "L028")
        figure = create_map(self.graph, path=result["path"], current_step=1,
                            start_id="L001", destination_id="L028", floor_filter=None)
        self.assertTrue(len(figure.data) > 5)
        self.assertTrue(any(trace.name == "Student agent" for trace in figure.data))
        floor_fig = create_map(self.graph, path=result["path"], floor_filter=2)
        self.assertFalse(any(trace.name == "Start" for trace in floor_fig.data))

    def test_direction_rows(self):
        result = find_route(self.graph, "L001", "L005")
        rows = route_rows(self.graph, result["path"], 0)
        self.assertEqual(rows[0]["Status"], "Current")
        self.assertEqual(rows[-1]["Node"], "L005")


if __name__ == "__main__":
    unittest.main()
