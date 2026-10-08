# NetBox Infrastructure Automation

Reference implementation for network discovery, inventory normalization, and safe source-of-truth reconciliation.

## Architecture documentation

See [Architecture and Design Decisions](docs/architecture.md) for the system diagram, component boundaries, failure handling, security model, and engineering tradeoffs.

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

## Live NetBox comparison (read-only)

The live comparison command retrieves device inventory from the NetBox REST API, follows pagination, and produces a JSON change plan. It does not write to NetBox.

Set credentials locally (never commit tokens):

```bash
export NETBOX_URL="https://netbox.example.com"
export NETBOX_TOKEN="your-token"
python -m src.compare_live
```

The token only needs read access to DCIM devices. Use a test instance or an explicitly authorized NetBox environment. The sample discovery fixture is compared by device name; mismatched site/role/type naming conventions may appear as proposed updates.

The API adapter requires HTTPS and rejects pagination redirects to other hosts. This example is a read-only reference implementation, not an approved production synchronization tool.

## Controlled synchronization demonstration

`src/controlled_sync.py` demonstrates approval gating, structured audit events, partial-failure handling, and rollback planning using **only in-memory synthetic inventory**. It cannot modify a live NetBox instance.

```bash
# Default: dry run, no changes
python -m src.controlled_sync

# Explicitly approve simulated changes
python -m src.controlled_sync --approve --approval-text "APPROVE DEMO SYNC"

# Write local JSONL audit events (ignored by Git)
python -m src.controlled_sync --audit-file output/sync-audit.jsonl
```

The rollback plan reverses completed simulated operations; it is not a production rollback mechanism. A production implementation would require object-ID resolution, NetBox-specific field validation, authorization, concurrency protection, persistent audit storage, and integration testing before enabling writes.
