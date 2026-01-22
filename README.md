# cogctrl (base repository)

Repo skeleton for a **repo-backed Cognitive Control System** with a **packet-based** engineering workflow.

## Key directories

- `.codex/skills/` — Codex-discoverable skills (per official Codex skills docs).
- `.codex/packet/` — Packet templates + shared packet assets (repo SSOT for packet content).
- `control/packet/` — Packet contracts + schemas (controller-side SSOT).
- `control/schemas/` — JSON Schemas for runtime artifacts (placeholder in this base repo).
- `control/catalog/` — Policies/catalogs (placeholder in this base repo).
- `tools/` — Deterministic controllers/validators (placeholder in this base repo).
- `ledger/` — Append-only logs / run artifacts (placeholder in this base repo).

## Next steps

1. Add Packet-0: `tools/packet_runner.py` (mechanical runner) and wire it into the `packet-runner` skill.
2. Add runtime schemas under `control/schemas/` (time_block, end_pointer, otest_result, preflight_snapshot).
3. Add policy/catalog YAML under `control/catalog/`.
