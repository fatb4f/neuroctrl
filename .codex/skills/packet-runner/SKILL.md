---
name: packet-runner
description: Run packet checks and emit evidence artifacts for a given control/packet contract.
metadata:
  short-description: Packet execution harness (scaffold)
---

## Scope
This is a **scaffold** skill: it should only touch the packet/execution scaffolding until the
deterministic runner exists.

## Allowed paths
- `.codex/**`
- `control/packet/**`
- `docs/**`

## Forbidden actions
- Do not add external dependencies
- Do not implement runtime tooling yet (no new executable logic under `tools/`)

## Intended workflow (once implemented)
- Validate a packet contract (JSON) against `control/packet/packet_contract.schema.json`
- Emit evidence JSON under `ledger/` or `execution/packets/`

## Notes
Add `tools/packet_runner.py` in a later packet and update this skill to invoke it.
