# Architecture (v0)

This repo implements a repo-backed supervisory control system that prevents MRV overshoot by enforcing
mechanical observability tests, schema-backed time-block contracts, and deterministic timer-to-timer
state transitions with an auditable ledger.

Core components:
- Human Plant Supervisor (fatigue/mode monotonicity + reset protocol)
- Execution Ledger Supervisor (block legality + event logging)
- Scheduler Gate (Context/Deferred legality windows)
- Policy + Catalog (deterministic mappings from observations to actions)
- Append-only artifacts / ledger (schemas, logs, end pointers)

Operating model:
- Work patterns: SYL (lower risk) vs CTX (high risk; legal only in Context Blocks or Deferred Windows)
- Control loop: preflight → Plan-Gen → execution ticks with O-tests and enforcement
- Coupling rule: ELS may only define/continue blocks at or below HPS recommended mode
- Domain isolation: engineering vs operations, one domain per packet by default
- Packet-based evolution: each packet adds a small mechanical capability with explicit scope boundaries

Detailed docs:
- `docs/architecture-outline.md` (full architecture outline)
- `docs/cognitive_control_system_v_0_architecture_and_requirements-v0.1.1.md` (requirements + packet plan)
