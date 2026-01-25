# cogctrl (base repository)

Repo skeleton for a **repo-backed Cognitive Control System** with a **packet-based** engineering workflow.

## Key directories

- `.codex/skills/` — Codex-discoverable skills.
- `.codex/packet/` — Packet templates + shared packet assets (SSOT for packet content).
- `.codex/tools/` — Canonical packet runner + gates + evidence collector.
- `.codex/packet/examples/` — Example packet contracts.
- `.codex/out/` — Evidence output (generated).
- `.codex/.worktrees/` — Packet worktrees (generated).
- `docs/` — Local documentation for this repo.
- `ledger/` — Placeholder for append-only logs / run artifacts.
- `tools/` — Local tooling notes (see `tools/README.md`).

## Typical usage

1. Create a contract under `.codex/packet/examples/<packet_id>.json`.
2. Run the packet runner via the skill script:
   `bash .codex/skills/packet-runner/scripts/run_packet.sh .codex/packet/examples/<packet_id>.json`
3. Review evidence under `.codex/out/<packet_id>/`.
