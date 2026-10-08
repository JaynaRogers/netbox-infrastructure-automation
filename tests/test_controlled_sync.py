"""Safety and failure-path tests for simulated synchronization."""
import unittest

from src.controlled_sync import APPROVAL_PHRASE, execute_demo, rollback_demo


class ControlledSyncTests(unittest.TestCase):
    def setUp(self):
        self.existing = [{"name": "fw-01", "management_ip": "192.0.2.1"}]
        self.discovered = [
            {"name": "fw-01", "management_ip": "192.0.2.2"},
            {"name": "fw-02", "management_ip": "192.0.2.3"},
        ]

    def test_default_is_read_only(self):
        _, inventory, audit, rollback = execute_demo(self.discovered, self.existing)
        self.assertEqual(inventory, self.existing)
        self.assertEqual(rollback, [])
        self.assertEqual(audit[0]["outcome"], "dry_run")

    def test_approval_phrase_is_required(self):
        _, inventory, _, rollback = execute_demo(
            self.discovered, self.existing, approve=True, approval_text="yes"
        )
        self.assertEqual(inventory, self.existing)
        self.assertFalse(rollback)

    def test_apply_and_rollback(self):
        _, inventory, audit, rollback = execute_demo(
            self.discovered, self.existing,
            approve=True, approval_text=APPROVAL_PHRASE
        )
        self.assertEqual(len(inventory), 2)
        self.assertEqual(len(rollback), 2)
        self.assertEqual(rollback_demo(inventory, rollback), self.existing)
        self.assertEqual([event["outcome"] for event in audit],
                         ["granted", "applied", "applied"])

    def test_partial_failure_has_recovery_plan(self):
        _, inventory, audit, rollback = execute_demo(
            self.discovered, self.existing, approve=True,
            approval_text=APPROVAL_PHRASE, fail_on="fw-01"
        )
        self.assertEqual(audit[-1]["outcome"], "failed")
        self.assertEqual(len(rollback), 1)
        self.assertEqual(rollback_demo(inventory, rollback), self.existing)

    def test_no_live_api_access(self):
        _, inventory, _, _ = execute_demo([], self.existing,
                                          approve=True, approval_text=APPROVAL_PHRASE)
        self.assertEqual(inventory, self.existing)


if __name__ == "__main__":
    unittest.main()
