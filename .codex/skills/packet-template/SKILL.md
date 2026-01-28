---
name: packet-template
description: Scaffold a packet contract example file from the SSOT template.
---

## Purpose
Scaffold a new packet contract example file from the SSOT template:
- `packet/examples/<packet_id>.json`

## Inputs
- `packet_id` (required)
- Optional overrides: `area`, `repo`, `base_ref`, `branch`
  - Default `base_ref`: `main`

## Outputs
- `packet/examples/<packet_id>.json`

## Notes
This skill does not execute packets; it only scaffolds the contract.
Use `packet-runner` to execute a packet.
SSOT templates live in `.codex/packet/`.
