
"""Infrastructure discovery through REST APIs."""

import json
import os
from pathlib import Path

import requests


def discover_from_fixture(path="examples/devices.json"):
    """Load synthetic infrastructure data for testing."""
    with Path(path).open(encoding="utf-8") as file:
        return json.load(file)


def discover_from_api():
    """Retrieve infrastructure inventory from a REST API."""
    base_url = os.environ["DISCOVERY_API_URL"].rstrip("/")
    token = os.environ["DISCOVERY_API_TOKEN"]

    response = requests.get(
        f"{base_url}/devices",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    response.raise_for_status()

    return response.json()


def normalize_devices(records):
    """Normalize discovered devices into a common model."""
    devices = []

    for record in records:
        devices.append({
            "name": record["name"],
            "serial": record.get("serial", ""),
            "site": record.get("site", "lab"),
            "role": record.get("role", "network"),
            "device_type": record.get("device_type", "generic"),
            "management_ip": record.get("management_ip"),
            "status": "active",
        })

    return devices


def main():
    mode = os.getenv("DISCOVERY_MODE", "fixture")

    if mode == "api":
        records = discover_from_api()
    else:
        records = discover_from_fixture()

    devices = normalize_devices(records)
    print(json.dumps(devices, indent=2))


if __name__ == "__main__":
    main()
