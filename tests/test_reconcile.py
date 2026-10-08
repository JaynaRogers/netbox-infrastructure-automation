"""Unit tests for read-only reconciliation behavior."""
import unittest

from src.reconcile import reconcile


class ReconciliationTests(unittest.TestCase):
    def test_creates_missing_device(self):
        plan = reconcile([{"name": "fw-lab-01"}], [])
        self.assertEqual([item["name"] for item in plan["create"]], ["fw-lab-01"])

    def test_updates_changed_management_ip(self):
        plan = reconcile(
            [{"name": "fw-lab-01", "management_ip": "192.0.2.10"}],
            [{"name": "fw-lab-01", "management_ip": "192.0.2.11"}],
        )
        self.assertEqual(plan["update"][0]["changes"]["management_ip"],
                         {"from": "192.0.2.11", "to": "192.0.2.10"})

    def test_unchanged_device(self):
        plan = reconcile([{"name": "router-01"}], [{"name": "router-01"}])
        self.assertEqual(plan["unchanged"], ["router-01"])

    def test_duplicate_names_are_rejected(self):
        with self.assertRaises(ValueError):
            reconcile([{"name": "fw-01"}, {"name": "fw-01"}], [])

    def test_missing_name_is_rejected(self):
        with self.assertRaises(ValueError):
            reconcile([{"serial": "DEMO-1"}], [])

    def test_no_automatic_deletion(self):
        plan = reconcile([], [{"name": "existing-01"}])
        self.assertEqual(plan, {"create": [], "update": [], "unchanged": []})


if __name__ == "__main__":
    unittest.main()
