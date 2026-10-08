"""Produce a dry-run comparison against a live NetBox API."""
import json

try:
    from src.discovery import discover_from_fixture, normalize_devices
    from src.netbox_snapshot import fetch_netbox_devices
    from src.reconcile import reconcile
except ModuleNotFoundError:
    from discovery import discover_from_fixture, normalize_devices
    from netbox_snapshot import fetch_netbox_devices
    from reconcile import reconcile


def main():
    desired = normalize_devices(discover_from_fixture())
    existing = fetch_netbox_devices()
    plan = reconcile(desired, existing)
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
