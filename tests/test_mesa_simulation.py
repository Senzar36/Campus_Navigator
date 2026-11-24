"""Mesa-specific smoke test; runs after installing requirements.txt."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

try:
    from simulation import CampusModel
except ImportError:
    CampusModel = None


@unittest.skipUnless(CampusModel is not None, 'Install Mesa from requirements.txt')
class TestMesaSimulation(unittest.TestCase):
    def test_agent_moves_one_node_at_a_time(self):
        model = CampusModel(['L001', 'L002', 'L003'])
        self.assertEqual(model.current_location_id, 'L001')
        self.assertFalse(model.finished)
        model.step()
        self.assertEqual(model.current_location_id, 'L002')
        model.step()
        self.assertEqual(model.current_location_id, 'L003')
        self.assertTrue(model.finished)
        model.step()
        self.assertEqual(model.current_location_id, 'L003')


if __name__ == '__main__':
    unittest.main()
