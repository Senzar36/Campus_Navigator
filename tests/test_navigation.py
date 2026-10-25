import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from graph import CampusGraph
from pathfinding import PathFinder
from navigation import Navigator

class TestNavigation(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        locations_file = os.path.join(base_dir, 'data', 'Campus_Navigator_Dataset.csv')
        connections_file = os.path.join(base_dir, 'data', 'campus_connections.csv')
        
        self.graph = CampusGraph(locations_file, connections_file)
        self.pf = PathFinder(self.graph)
        self.nav = Navigator(self.pf)

    def test_direct_route(self):
        path, cost = self.nav.calculate_route(['L001', 'L005'])
        self.assertIsNotNone(path)
        self.assertEqual(path[0], 'L001')
        self.assertEqual(path[-1], 'L005')
        self.assertGreater(cost, 0)

    def test_walkway_and_ramp_distances(self):
        path, cost = self.nav.calculate_route(['L003', 'L033'])
        self.assertEqual(path, ['L003', 'L033'])
        self.assertAlmostEqual(cost, 10.0)

        path, cost = self.nav.calculate_route(['L003', 'L035', 'L033'])
        self.assertEqual(path, ['L003', 'L035', 'L033'])
        self.assertAlmostEqual(cost, 11.39)

    def test_intermediate_stop(self):
        path, cost = self.nav.calculate_route(['L001', 'L004', 'L005'])
        self.assertIsNotNone(path)
        self.assertLess(path.index('L004'), path.index('L005'))
        self.assertEqual(path[0], 'L001')
        self.assertEqual(path[-1], 'L005')
        
    def test_identical_start_and_dest(self):
        path, cost = self.nav.calculate_route(['L001', 'L001'])
        self.assertEqual(path, ['L001'])
        self.assertEqual(cost, 0)

    def test_invalid_start_location(self):
        with self.assertRaises(ValueError):
            self.nav.calculate_route(['INVALID', 'L005'])

    def test_invalid_destination(self):
        with self.assertRaises(ValueError):
            self.nav.calculate_route(['L001', 'INVALID'])

    def test_unreachable_destination(self):
        original_connections = {
            location_id: edges.copy()
            for location_id, edges in self.graph.adjacency_list.items()
        }

        try:
            self.graph.adjacency_list['L031'] = []

            for location_id, edges in self.graph.adjacency_list.items():
                self.graph.adjacency_list[location_id] = [
                    (neighbor, weight)
                    for neighbor, weight in edges
                    if neighbor != 'L031'
                ]

            path, cost = self.nav.calculate_route(['L001', 'L031'])

            self.assertIsNone(path)
            self.assertEqual(cost, 0)

        finally:
            self.graph.adjacency_list = original_connections

    def test_missing_connection_in_route_raises_error(self):
        self.pf.a_star = lambda start_id, goal_id: ['L001', 'L005']

        self.graph.adjacency_list['L001'] = [
            (neighbor, weight)
            for neighbor, weight in self.graph.adjacency_list['L001']
            if neighbor != 'L005'
        ]

        with self.assertRaisesRegex(ValueError, 'no connection'):
            self.nav.calculate_route(['L001', 'L005'])

if __name__ == '__main__':
    unittest.main()