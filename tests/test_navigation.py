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

    def test_intermediate_stop(self):
        path, cost = self.nav.calculate_route(['L001', 'L004', 'L005'])
        self.assertIsNotNone(path)
        self.assertIn('L004', path)
        self.assertEqual(path[0], 'L001')
        self.assertEqual(path[-1], 'L005')
        
    def test_identical_start_and_dest(self):
        path, cost = self.nav.calculate_route(['L001', 'L001'])
        self.assertEqual(path, ['L001'])
        self.assertEqual(cost, 0)

if __name__ == '__main__':
    unittest.main()