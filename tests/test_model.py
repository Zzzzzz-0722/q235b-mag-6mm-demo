import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "q235b_model"))

from model import Conditions, recommend


class ReferenceSelectionTests(unittest.TestCase):
    def test_default_retrieves_wire_as_output(self):
        result = recommend(Conditions())
        self.assertEqual(result["status"], "reference_matches")
        self.assertEqual([r["wire_diameter_mm"] for r in result["matches"]], [1.1])

    def test_overlapping_gap_shows_both_processes(self):
        result = recommend(Conditions(root_gap_mm=1.3))
        self.assertEqual([r["source_id"] for r in result["matches"]],
                         ["LINCOLN-GMAW-6MM-CO2", "OTC-CO2-6MM-I-2PASS"])
        self.assertEqual([r["wire_diameter_mm"] for r in result["matches"]], [1.1, 1.2])

    def test_v_joint_is_labeled_as_ss400_analogy(self):
        result = recommend(Conditions(joint="单V形对接", gas="82% Ar + 18% CO₂", root_gap_mm=2))
        self.assertEqual(result["matches"][0]["source_id"], "JAES-SS400-6MM-500")
        self.assertEqual(result["matches"][0]["source_material"], "SS400")
        self.assertEqual(result["matches"][0]["groove_angle_deg"], 60)

    def test_unsupported_condition_does_not_generate_parameters(self):
        for c in (Conditions(thickness_mm=8), Conditions(joint="单V形对接"),
                  Conditions(root_gap_mm=1.7)):
            self.assertEqual(recommend(c)["matches"], [])


if __name__ == "__main__":
    unittest.main()
