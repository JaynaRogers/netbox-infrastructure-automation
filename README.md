# NetBox Infrastructure Automation

Reference implementation for network discovery, inventory normalization, and safe source-of-truth reconciliation.

## Capabilities

- Discover network devices from synthetic JSON fixtures or a configurable REST endpoint.
- Normalize discovered device records into a consistent inventory model.
- Export NetBox device inventory to CSV with `pynetbox`.
- Generate deterministic, **read-only** reconciliation plans identifying devices to create, update, or leave unchanged.
- Reject duplicate or missing device names. Never automatically delete inventory records.
- Run unit tests through GitHub Actions.

## Architecture

```text
Discovery fixture / REST API
            |
            v
  Inventory normalization
            |
            v
 Read-only reconciliation <--- Existing inventory snapshot
            |
            v
   JSON change plan (dry run)
```

The REST discovery adapter expects a generic `GET /devices` endpoint returning a JSON list; provider-specific adapters, pagination, and production API integrations are not implemented. The reconciliation planner uses a local synthetic NetBox snapshot rather than writing to a live NetBox instance.

## Quick start

Requires Python 3.10 or newer.

```bash
python -m pip install -r requirements.txt
python src/discovery.py
python src/reconcile.py
python -m unittest discover -s tests -v
```

To export a real NetBox inventory, set `NETBOX_URL` and `NETBOX_TOKEN` in your local environment, then run:

```bash
python src/netbox_inventory.py
```

Keep credentials out of version control. Exported inventory may contain sensitive infrastructure details; do not commit it to a public repository.

## Example reconciliation

The synthetic inventory demonstrates a device that is unchanged, a device with a changed management IP, and new devices requiring creation. The planner reports proposed differences but makes no changes.

## Security

All committed sample inventory is fictional and uses reserved documentation address ranges. This repository does not contain production infrastructure details, customer data, access tokens, or proprietary configurations.

## License

MIT.
