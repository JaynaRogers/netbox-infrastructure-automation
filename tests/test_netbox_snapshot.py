"""Mocked tests for live NetBox API inventory pagination."""
import unittest
from unittest.mock import Mock

from src.netbox_snapshot import fetch_netbox_devices, normalize_netbox_device


class NetBoxSnapshotTests(unittest.TestCase):
    def test_normalizes_netbox_fields(self):
        record = normalize_netbox_device({
            "name": "fw-lab-01", "serial": "DEMO-001",
            "site": {"slug": "denver-lab"},
            "role": {"slug": "firewall"},
            "device_type": {"model": "fortigate-vm"},
            "primary_ip4": {"address": "192.0.2.10/24"},
            "status": {"value": "active"},
        })
        self.assertEqual(record["management_ip"], "192.0.2.10")
        self.assertEqual(record["role"], "firewall")

    def test_fetches_multiple_pages(self):
        session = Mock()
        first = Mock()
        first.json.return_value = {
            "results": [{"name": "fw-01"}],
            "next": "https://netbox.example.com/api/dcim/devices/?limit=100&offset=100",
        }
        second = Mock()
        second.json.return_value = {"results": [{"name": "fw-02"}], "next": None}
        session.get.side_effect = [first, second]
        devices = fetch_netbox_devices(
            "https://netbox.example.com", "DEMO-TOKEN", session=session
        )
        self.assertEqual([device["name"] for device in devices], ["fw-01", "fw-02"])
        self.assertEqual(session.get.call_count, 2)

    def test_rejects_external_pagination(self):
        session = Mock()
        response = Mock()
        response.json.return_value = {
            "results": [],
            "next": "https://other.example.com/api/dcim/devices/",
        }
        session.get.return_value = response
        with self.assertRaises(ValueError):
            fetch_netbox_devices("https://netbox.example.com", "DEMO", session=session)
        self.assertEqual(session.get.call_count, 1)

    def test_requires_https(self):
        with self.assertRaises(ValueError):
            fetch_netbox_devices("http://netbox.example.com", "DEMO", session=Mock())


if __name__ == "__main__":
    unittest.main()
