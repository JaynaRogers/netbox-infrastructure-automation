"""Approval-gated inventory synchronization simulator.

This module intentionally has no NetBox write client. It executes against an
in-memory inventory and records reversible changes for review and testing.
"""
import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

from src.discovery import discover_from_fixture, normalize_devices
from src.reconcile import reconcile

APPROVAL_PHRASE = "APPROVE DEMO SYNC"


def _event(action, name, outcome, details=None):
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "device": name,
        "outcome": outcome,
        "details": details or {},
    }


def execute_demo(discovered, existing, *, approve=False, approval_text=None, fail_on=None):
    """Plan changes, then optionally apply to a private in-memory copy.

    Returns (plan, resulting_inventory, audit_events, rollback_plan).
    No external API writes are possible from this function.
    """
    plan = reconcile(discovered, existing)
    inventory = {item["name"]: copy.deepcopy(item) for item in existing}
    audit = []
    rollback = []
    changes = len(plan["create"]) + len(plan["update"])
    if not approve or approval_text != APPROVAL_PHRASE:
        audit.append(_event("approval", "", "dry_run", {"proposed_changes": changes}))
        return plan, list(inventory.values()), audit, rollback

    audit.append(_event("approval", "", "granted", {"proposed_changes": changes}))
    for record in plan["create"]:
        name = record["name"]
        if name == fail_on:
            audit.append(_event("create", name, "failed", {"reason": "simulated failure"}))
            break
        inventory[name] = copy.deepcopy(record)
        rollback.append({"action": "remove_created", "name": name})
        audit.append(_event("create", name, "applied"))
    else:
        for change in plan["update"]:
            name = change["name"]
            if name == fail_on:
                audit.append(_event("update", name, "failed", {"reason": "simulated failure"}))
                break
            before = copy.deepcopy(inventory[name])
            for field, difference in change["changes"].items():
                inventory[name][field] = difference["to"]
            rollback.append({"action": "restore", "name": name, "record": before})
            audit.append(_event("update", name, "applied",
                                {"fields": sorted(change["changes"])}))
    return plan, list(inventory.values()), audit, rollback


def rollback_demo(inventory, rollback_plan):
    """Reverse successful demo operations, in reverse execution order."""
    devices = {item["name"]: copy.deepcopy(item) for item in inventory}
    for operation in reversed(rollback_plan):
        if operation["action"] == "remove_created":
            devices.pop(operation["name"], None)
        elif operation["action"] == "restore":
            devices[operation["name"]] = copy.deepcopy(operation["record"])
        else:
            raise ValueError("Unknown rollback operation")
    return list(devices.values())


def main():
    parser = argparse.ArgumentParser(description="Simulated, approval-gated inventory sync")
    parser.add_argument("--approve", action="store_true", help="Enable demo changes")
    parser.add_argument("--approval-text", default="", help="Exact approval phrase")
    parser.add_argument("--audit-file", type=Path, help="Optional local JSONL audit path")
    args = parser.parse_args()
    discovered = normalize_devices(discover_from_fixture())
    existing = json.loads(Path("examples/netbox_snapshot.json").read_text(encoding="utf-8"))
    plan, inventory, audit, rollback = execute_demo(
        discovered, existing, approve=args.approve, approval_text=args.approval_text
    )
    print(json.dumps({
        "mode": "simulated_apply" if rollback else "dry_run",
        "plan": plan,
        "audit": audit,
        "rollback_plan": rollback,
        "resulting_inventory": inventory,
    }, indent=2))
    if args.audit_file:
        args.audit_file.parent.mkdir(parents=True, exist_ok=True)
        with args.audit_file.open("a", encoding="utf-8") as handle:
            for event in audit:
                handle.write(json.dumps(event) + "\n")


if __name__ == "__main__":
    main()
