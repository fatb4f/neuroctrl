# Architecture Outline (v0)

## 1) Architecture outline

### 1.1 System goal
A repo-backed supervisory control system that prevents MRV overshoot by:
- enforcing **mechanical observability tests** (O-tests),
- gating work via **schema-backed time-block contracts**,
- coupling a **Human Plant Supervisor** (fatigue/mode) with an **Execution Ledger Supervisor** (legality/ledger),
- ensuring deterministic **timer-to-timer** state transitions and audit logging.

### 1.2 Components

#### A) Human Plant Supervisor (HPS)
**Responsibility:** classify fatigue and enforce mode monotonicity.
- **State:** `(mode ∈ {GREEN,YELLOW,RED}, fatigue_band ∈ {OK,RISING,NEAR_LIMIT}, timer_phase ∈ {WORK,RESET_SHORT,RESET_LONG})`
- **Inputs:** O-tests results, friction triggers, timer events, previous end pointer (mode/band at end)
- **Outputs:** `downgrade_mode`, `force_close_block`, `run_reset_protocol`, `recommend_next_mode`

#### B) Execution Ledger Supervisor (ELS)
**Responsibility:** prevent illegal work by requiring a valid active block contract and logging state.
- **State:** `(block_state ∈ {UNDEFINED,DEFINED,CLOSED}, active_block_id?, timer_phase)`
- **Inputs:** plan proposals, schedule gates (Context/Deferred windows), previous end pointer, HPS snapshot
- **Outputs:** `define_block/deny_block`, `enforce_boundary`, `append_event`, `close_block`, `emit_end_pointer`

#### C) Scheduler Gate (SG)
**Responsibility:** declare legality windows.
- **Inputs:** weekly schedule template (Deferred Windows, Context Blocks)
- **Outputs:** `is_context_block`, `is_deferred_window`

#### D) Policy + Catalog (PC)
**Responsibility:** deterministic mapping from observations to actions.
- O-tests catalog (procedures, pass/fail criteria)
- classifier (FAIL count → fatigue_band)
- action policy (band/mode/window → required outputs)

#### E) Artifacts / Ledger
**Responsibility:** auditable SSOT of execution.
- schemas: `time_block`, `end_pointer`, `otest_result`, `preflight_snapshot`
- append-only session log events
- `deferred.md` with tags `[MECH]/[SYL]/[CTX]`

### 1.3 Coupling / dependency
- HPS produces **max allowed intensity** (`recommended_mode`, `band`).
- ELS may only define/continue a block whose `mode_at_start ≤ recommended_mode` and whose pattern legality passes SG.

### 1.4 Work pattern classes
- **SYL (lower MRV risk):** INF* syllabus-aligned work.
- **CTX (high MRV risk):** contextual work around syllabus; legal only in Context Blocks or Deferred Windows.

### 1.5 Control loop sequence

#### Preflight (before Plan-Gen)
1. Run O-tests → classify band.
2. Apply monotone mode rule from `prev_end_pointer`.
3. Emit `preflight_snapshot`.

#### Plan-Gen (2–3 hours)
- Generate ≤3 blocks, each with a block contract.
- Enforce legality: at most one CTX block/day; CTX only inside scheduled windows.

#### Execution (timer-to-timer)
- On each work tick end: reset + O-tests + reclassify + enforce downgrades/close.
- ELS logs each tick and emits end pointers on close.

---

## 2) Tooling selection and scope

### 2.1 Tooling options (repo-backed)

#### Option A: Local repo + Python tools (primary)
- `python` scripts provide deterministic gates and logging.
- LLM (ChatGPT/Codex) generates proposals only.

#### Option B: Codex CLI + repo (executor)
- Best for applying multi-file changes and maintaining skill-based constraints.
- Works well with existing CBIA/Codex discipline.

#### Option C: ChatGPT CLI + repo (planner)
- Best for interactive plan-gen and spec iteration.

### 2.2 Scope boundaries (v0)

#### In-scope
- Schema definitions
- Tooling to validate and generate block contracts
- O-test prompts + result logging
- Mode/band policy enforcement
- Deferred windows / context legality gating
- Append-only ledger and end pointers

#### Out-of-scope (v0)
- Direct GitHub Projects automation (optional later)
- Full calendar integration (gcal/ifttt) (later)
- ML-based prediction of MRV (not required)
- Fine-grained biometric sensing (optional later)

### 2.3 Recommended split of responsibilities
- **LLM:** propose plans/blocks, draft docs.
- **Repo tools:** decide legality/validity, enforce gates, write logs.

---

## 3) Engineering requirements: coverage + gaps

### 3.1 Requirements (E)

#### E1 Deterministic state representation
- All controller-relevant state is serializable: mode, band, timer_phase, block_state.

#### E2 Schema-backed contracts
- `time_block` and `end_pointer` must validate with JSON Schema.

#### E3 Deterministic policy evaluation
- O-tests → band classifier is deterministic.
- band/mode/window → actions are deterministic.

#### E4 Timer-to-timer transitions
- Both supervisors advance state on each timer event.

#### E5 Auditability
- Append-only event log with timestamps and summaries.
- Evidence artifacts referenced by path/id.

#### E6 Boundary enforcement
- Block contract declares allowed paths + illegal moves.
- Tool denies actions outside the boundary (initially as policy + review; later as repo-level checks).

#### E7 Tool ergonomics
- Commands are single-shot, low-friction, minimal prompts.

### 3.2 Current coverage
- Conceptual model defined (HPS/ELS + timer-to-timer).
- O-tests proposed and classifier defined.
- Issue schema drafted and separated from validation tooling.

### 3.3 Gaps (engineering)
- Implement JSON Schemas for `time_block`, `end_pointer`, `otest_result`, `preflight_snapshot`.
- Implement deterministic policy files (`otests.yaml`, `policy.yaml`, `schedule.yaml`).
- Implement toolchain:
  - `preflight_eval.py`
  - `plan_gen.py` (proposal only)
  - `define_block.py` / `validate_block.py`
  - `close_block.py`
  - `append_event.py` (or integrated)
  - `validate_issue.py` (workflow policy)
- Define a canonical log/event format and storage layout.
- Define and implement GitHub integration adapter:
  - MCP-backed or `gh`-CLI-backed tool (`sync_github.py`)
  - Explicit allow-list of operations (comment, label transition, PR open/close)
  - Mapping from ledger checkpoints → issue state updates

---

## 4) Operations requirements: coverage + gaps

### 4.1 Requirements (O)

#### O1 Simple daily operation
- Start-of-session: `preflight` → `plan-gen` → `define-block`.
- During session: timer rings → reset + (mini) O-tests + log.
- End-of-session: close block → emit end pointer.

#### O2 Weekly cadence support
- Deferred Windows 2x/week (60–90m) with triage/execute/stabilize.
- Context Blocks scheduled explicitly; CTX illegal otherwise.

#### O3 Failure modes are safe
- If uncertain PASS/FAIL → treat as FAIL.
- If schema invalid or missing block → notes-only.

#### O4 Minimal cognitive overhead
- Logging is 1-line.
- O-tests are ≤60s.

#### O5 Portability
- Works offline in a local repo.

### 4.2 Current coverage
- Reset oscillator protocol defined.
- Deferred window rules defined.
- Mode monotonicity rule defined.

### 4.3 Gaps (operations)
- Define exact CLI commands and defaults.
- Define the "notes-only" fallback workflow.
- Define weekly schedule template and how it is stored/edited.
- Define how to select ≤2 deferred items and record selection.
- Define housekeeping: archive logs, rotate sessions, backups.

---

## 5) Implementation plan (Codex CLI + packet execution)

### 5.1 Execution model

#### Roles
- **Codex CLI (executor):** applies repo changes under skill constraints, produces artifacts, opens PRs if desired.
- **Repo tools (controllers):** deterministic gates (schemas/policy/validators). Codex does not decide legality.
- **You (supervisor):** selects packet, reviews end-state evidence, merges/promotes.

#### Domain isolation (hard requirement)
- **Engineering domain:** code, schemas, validators, skills, CI gates, GitHub adapter.
- **Operations domain:** runbooks, schedules, daily/weekly procedures, human-facing checklists.
- Cross-domain changes must be explicit and rare (single packet with dual sign-off). Default: **one domain per packet**.

#### Repository structure (target)
```text
neuroctrl/
  .codex/
    skills/
      packet-runner/
        SKILL.md
        skill.json
        scripts/
      packet-01-foundation/
      packet-02-schemas/
      packet-03-policy-catalog/
      packet-04-tools-core/
      packet-05-ci-gates/
      packet-06-github-adapter/
      packet-07-ops-runbooks/
  control/
    schemas/
    catalog/
  tools/
  ledger/
  docs/
```

### 5.2 Codex packet workflow

#### Packet lifecycle
1. **Select packet** (one domain).
2. Ensure packet contract exists at `control/packets/<packet-id>.md`.
3. Run Codex with the packet skill only (no free-form).
4. Codex outputs artifacts + evidence into repo.
5. Run mechanical validation locally/CI.
6. Promote by merge/tag once end-state predicate holds.

#### Packet contract fields (required)
Each `control/packets/<packet-id>.md` must specify:
- **Purpose / scope boundary**
- **Inputs** (files, existing dirs)
- **Outputs** (exact paths)
- **End-state predicate** (mechanical checks)
- **Evidence artifacts** (validator outputs)
- **Failure modes / rollback**
- **Forbidden actions** (network, unrelated refactors, etc.)

#### Skill model
- One skill per packet: `.codex/skills/<packet-id>/SKILL.md + skill.json + scripts/`
- Skill must declare allowed paths, required outputs, and required validation commands.
- Skill must include a regen-and-compare rule for any generated views (Mermaid, derived docs).

### 5.3 Engineering packets (architecture + workflow definitions)

#### Packet 0: Packet runner baseline (engineering)
**Goal:** deterministic execution harness for packets.
- Outputs:
  - `.codex/skills/packet-runner/*`
  - `tools/packet_runner.py` (runs packet checks + emits evidence JSON)
  - `control/packets/packet_contract.schema.json` + example
- End-state:
  - `python tools/packet_runner.py --self-test` passes

#### Packet 1: Repo foundation + namespaces (engineering)
**Goal:** establish directories, SSOT locations, and no-hand-edit rules.
- Outputs: `control/`, `tools/`, `ledger/`, `docs/` skeletons
- End-state: tree exists; lint/format baseline

#### Packet 2: Controller schemas (engineering)
**Goal:** JSON Schemas for controller artifacts.
- Outputs:
  - `control/schemas/time_block.schema.json`
  - `control/schemas/end_pointer.schema.json`
  - `control/schemas/otest_result.schema.json`
  - `control/schemas/preflight_snapshot.schema.json`
- End-state:
  - `python tools/validate.py --schemas` passes
  - sample artifacts validate

#### Packet 3: Policy catalog (engineering)
**Goal:** deterministic catalogs for O-tests, classifier, schedule gates.
- Outputs:
  - `control/catalog/otests.yaml`
  - `control/catalog/policy.yaml`
  - `control/catalog/schedule.yaml`
- End-state:
  - `python tools/validate.py --policy` passes

#### Packet 4: Core tools (engineering)
**Goal:** implement deterministic tools (no GitHub).
- Outputs:
  - `tools/preflight_eval.py`
  - `tools/define_block.py` / `tools/validate_block.py`
  - `tools/otest.py`
  - `tools/close_block.py`
  - `tools/append_event.py` (or integrated)
- End-state:
  - end-to-end local flow works: preflight → define → 2 ticks logged → close emits end pointer

#### Packet 5: CI gates (engineering)
**Goal:** ensure every push enforces invariants.
- Outputs:
  - `.github/workflows/validate.yml`
  - `tools/ci/validate_repo.py` (schema + policy + log format)
- End-state:
  - CI passes on clean branch; fails on known-bad fixtures

#### Packet 6: GitHub integration adapter (engineering)
**Goal:** optional actuator layer (MCP or gh) consuming checkpoints.
- Outputs:
  - `control/schemas/checkpoint.schema.json`
  - `tools/emit_checkpoint.py`
  - `tools/sync_github.py` (MCP/gh backend abstraction)
  - `control/catalog/github_ops_allowlist.yaml`
- End-state:
  - dry-run prints intended ops
  - real run posts comment + labels (if creds available)

### 5.4 Operations packets (domain-isolated)

#### Packet 7: Ops runbooks + schedules (operations)
**Goal:** human-facing procedures with minimal cognitive overhead.
- Outputs:
  - `docs/runbook_daily.md` (preflight → plan → execute → close)
  - `docs/runbook_weekly.md` (Deferred Windows + Context Blocks)
  - `docs/notes_only_fallback.md`
  - `docs/deferred_triage.md`
- End-state:
  - runbooks reference only stable tool interfaces
  - no engineering changes (paths/commands must already exist)

### 5.5 Promotion / stabilization

#### Versioning
- Tag milestones: `cogctrl/v0.1.0` after Packet 4.
- Tag `v0.2.0` after CI + GitHub adapter.

#### Evidence ledger
- Each packet run emits `execution/packets/<packet-id>/evidence.json` with:
  - inputs manifest
  - outputs manifest
  - validation command outputs
  - git diff summary

---

## Next deliverable

- Implement Packet 0 contract + skill (packet runner baseline), then proceed in order: 1 → 2 → 3 → 4 → 5 → 6 → 7.
