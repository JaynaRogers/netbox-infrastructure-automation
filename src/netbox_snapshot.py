"""Read a live NetBox inventory through its REST API, without mutations."""
import ipaddress
import os

import requests


def _label(value):
    if isinstance(value, dict):
        return value.get("slug") or value.get("name") or value.get("value") or ""
    return value or ""


def normalize_netbox_device(device):
    """Convert a NetBox device response to the discovery comparison model."""
    address = device.get("primary_ip4") or device.get("primary_ip")
    if isinstance(address, dict):
        address = address.get("address")
    if address:
        address = str(ipaddress.ip_interface(address).ip)
    device_type = device.get("device_type") or {}
    if isinstance(device_type, dict):
        device_type = device_type.get("model") or device_type.get("slug") or ""
    return {
        "name": device["name"],
        "serial": device.get("serial") or "",
        "site": _label(device.get("site")),
        "role": _label(device.get("role") or device.get("device_role")),
        "device_type": device_type,
        "management_ip": address,
        "status": _label(device.get("status")),
    }


def fetch_netbox_devices(base_url=None, token=None, session=None):
    """Fetch every device page from NetBox; only follow links on the same host."""
    from urllib.parse import urljoin, urlparse

    base_url = (base_url or os.environ["NETBOX_URL"]).rstrip("/")
    token = token or os.environ["NETBOX_TOKEN"]
    if not base_url.startswith("https://"):
        raise ValueError("NETBOX_URL must use HTTPS")
    origin = urlparse(base_url)
    endpoint = base_url + "/api/dcim/devices/?limit=100"
    client = session or requests.Session()
    results = []
    visited = set()
    while endpoint:
        if endpoint in visited:
            raise ValueError("NetBox pagination loop detected")
        visited.add(endpoint)
        parsed = urlparse(endpoint)
        if parsed.scheme != "https" or parsed.netloc != origin.netloc:
            raise ValueError("NetBox pagination URL points outside the configured host")
        response = client.get(
            endpoint,
            headers={"Authorization": f"Token {token}", "Accept": "application/json"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
            raise ValueError("Unexpected NetBox API response")
        results.extend(normalize_netbox_device(item) for item in payload["results"])
        next_page = payload.get("next")
        endpoint = urljoin(endpoint, next_page) if next_page else None
    return results
