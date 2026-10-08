"""Compare normalized discovery records with a NetBox inventory snapshot.

Read-only planning: this module never changes NetBox.
"""
import json
from pathlib import Path

FIELDS = ("serial", "site", "role", "device_type", "management_ip", "status")


def reconcile(discovered, existing):
    """Return deterministic create/update/unchanged plans keyed by device name."""
    def index(records, label):
        result = {}
        for record in records:
            name = record.get("name")
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"{label} contains a device without a valid name")
            if name in result:
                raise ValueError(f"Duplicate device name in {label}: {name}")
            result[name] = record
        return result

    desired = index(discovered, "discovered inventory")
    current = index(existing, "existing inventory")
    plan = {"create": [], "update": [], "unchanged": []}
    for name in sorted(desired):
        candidate = desired[name]
        if name not in current:
            plan["create"].append(candidate)
            continue
        changes = {
            field: {"from": current[name].get(field), "to": candidate.get(field)}
            for field in FIELDS
            if current[name].get(field) != candidate.get(field)
        }
        if changes:
            plan["update"].append({"name": name, "changes": changes})
        else:
            plan["unchanged"].append(name)
    return plan


def main():
    from discovery import discover_from_fixture, normalize_devices

    discovered = normalize_devices(discover_from_fixture())
    existing_path = Path("examples/netbox_snapshot.json")
    existing = json.loads(existing_path.read_text(encoding="utf-8"))
    print(json.dumps(reconcile(discovered, existing), indent=2))


if __name__ == "__main__":
    main()
