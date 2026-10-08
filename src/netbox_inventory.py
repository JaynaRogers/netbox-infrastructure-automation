
import csv
import os
from pathlib import Path

import pynetbox
from dotenv import load_dotenv


def get_netbox_client():
    """Connect to NetBox using environment credentials."""
    load_dotenv()

    url = os.environ["NETBOX_URL"]
    token = os.environ["NETBOX_TOKEN"]

    return pynetbox.api(url, token=token)


def export_inventory(client, output_file="output/inventory.csv"):
    """Export device inventory from NetBox to CSV."""
    devices = client.dcim.devices.all()
    destination = Path(output_file)
    destination.parent.mkdir(parents=True, exist_ok=True)

    count = 0

    with destination.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "name",
            "site",
            "role",
            "device_type",
            "status",
            "primary_ip",
        ])

        for device in devices:
            writer.writerow([
                device.name,
                str(device.site),
                str(device.role),
                str(device.device_type),
                str(device.status),
                str(device.primary_ip4 or ""),
            ])
            count += 1

    print(f"Exported {count} devices to {destination}")


if __name__ == "__main__":
    netbox = get_netbox_client()
    export_inventory(netbox)

