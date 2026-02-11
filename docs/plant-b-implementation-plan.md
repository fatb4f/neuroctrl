# Plant B implementation plan (v0)

Plant B covers project-specific engineering + operations work outside the shared `.codex/` Plant A subtree.
This plan follows domain isolation (engineering vs operations) and prefers mechanical checks over narrative claims.

## 1) Scope and assumptions
- **Plant A (shared):** `.codex/` subtree (skills, packet infra, shared workflow patterns).
- **Plant B (project-specific):** `control/`, `tools/`, `docs/`, `ledger/`, and any project-specific CI or templates.
- **Domain isolation:** engineering and operations changes stay in separate packets by default.

## 1.1 Planned names (subject to definition in packets below)
- Planned validator command: `python <planned> tools/validate.py --<scope>` (final name defined in B3/B4)
- Planned evidence root (Plant B): `ledger/packets/<packet-id>/evidence.json`
- Catalog schema choice: v0 prefers a single `catalog.schema.json`; split per-catalog schemas allowed if complexity grows.

## 2) Engineering plan (Plant B)

### Packet B1: Repo layout + schemas
**Goal:** establish the project-specific schema SSOT and layout.
- Outputs:
  - `control/schemas/time_block.schema.json`
  - `control/schemas/end_pointer.schema.json`
  - `control/schemas/otest_result.schema.json`
  - `control/schemas/preflight_snapshot.schema.json`
  - `control/schemas/catalog.schema.json` (or `policy.schema.json`, `otests.schema.json`, `schedule.schema.json`)
- End-state checks:
  - `python <planned> tools/validate.py --schemas` passes
  - sample fixtures validate

### Packet B2: Policy + schedule catalogs
**Goal:** deterministic catalogs for O-tests, policy, and schedule gates.
- Outputs:
  - `control/catalog/otests.yaml`
  - `control/catalog/policy.yaml`
  - `control/catalog/schedule.yaml`
- End-state checks:
  - catalog files validate against `control/schemas/catalog.schema.json` (or per-catalog schemas)
  - `python <planned> tools/validate.py --policy` passes

### Packet B3: Ledger format + event taxonomy
**Goal:** canonical log/event format and storage layout.
- Outputs:
  - `ledger/README.md`
  - `control/schemas/event.schema.json` (or `ledger_event.schema.json`)
  - log path conventions (session, tick, event)
  - event taxonomy:
    - `event_type ∈ {TICK_END, RESET_START, RESET_END, BLOCK_DEFINED, BLOCK_DENIED, BLOCK_CLOSED, CHECKPOINT_EMITTED}`
    - required fields: `ts`, `timer_phase`, `mode`, `fatigue_band`, `block_id`, `event_type`
    - optional fields: `otest_summary`, `reason`
- End-state checks:
  - `python <planned> tools/validate.py --ledger` passes

### Packet B4: Core controllers and validators
**Goal:** implement deterministic tooling (no external integrations) against the canonical ledger.
- Outputs:
  - `tools/preflight_eval.py`
  - `tools/define_block.py`
  - `tools/validate_block.py`
  - `tools/otest.py`
  - `tools/append_event.py`
  - `tools/close_block.py`
- End-state checks:
  - dry-run path works: preflight → define → 2 ticks logged → close emits end pointer

### Packet B5: CI gates (project-specific)
**Goal:** enforce invariants on every push.
- Outputs:
  - `.github/workflows/validate.yml`
  - `tools/ci/validate_repo.py`
- End-state checks:
  - CI passes on clean branch; fails on known-bad fixtures

### Packet B6: Optional integration adapters
**Goal:** project-specific actuators and adapters with explicit contracts.
- Inputs:
  - `checkpoint.json` (schema-validated)
- Outputs (optional):
  - `tools/sync_github.py` or other adapters
  - `control/catalog/ops_allowlist.yaml`
- Allowed ops (allowlist):
  - `comment`, `label_add`, `label_remove`, `close_via_pr_only`, `project_update` (best-effort)
- Forbidden ops:
  - changing contract fields
  - upgrading workflow_state without evidence
- End-state checks:
  - dry-run prints intended ops

## 3) Operations plan (Plant B)

### Packet B7: Daily + weekly runbooks
**Goal:** human-facing procedures with minimal cognitive overhead.
- Outputs:
  - `docs/runbook_daily.md`
  - `docs/runbook_weekly.md`
  - `docs/notes_only_fallback.md`
  - `docs/deferred_triage.md`
- End-state checks:
  - runbooks reference only stable tool interfaces
  - no engineering changes in this packet

### Packet B8: Ops verification checklist
**Goal:** lightweight, repeatable ops checks.
- Outputs:
  - `docs/ops_verification.md`
- End-state checks:
  - checklist references concrete commands and expected artifacts

## 4) Ordering + guardrails
- Default execution order: B1 → B2 → B3 → B4 → B5 → B7 → B8 → (optional B6).
- Engineering and operations remain domain-isolated unless explicitly combined.
- Every packet emits evidence under `ledger/packets/<packet-id>/evidence.json`.

## 5) Evidence template (per packet)
Each packet emits a single evidence artifact with:
- inputs manifest
- outputs manifest
- validation command outputs
- git diff summary
- content hash of outputs (recommended)
