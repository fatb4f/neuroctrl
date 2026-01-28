# Architecture (v0)

This repo is intended to implement a repo-backed supervisory control system with:

- Human Plant Supervisor (fatigue/mode)
- Execution Ledger Supervisor (legality/ledger)
- Scheduler Gate (Context/Deferred legality windows)
- Policy + Catalog (deterministic mapping)
- Append-only artifacts / ledger

Packet-based evolution is expected: each packet adds a small mechanical capability, with explicit scope boundaries.

See `docs/architecture-outline.md` for the full system architecture and execution plan.
