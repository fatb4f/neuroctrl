---
name: packet-001-copier-consumption
description: Define and document the copier template consumption strategy for the live neuroctrl repo.
metadata:
  short-description: Copier consumption strategy planning
---

## Scope
- Define the consumption strategy and update policy for the cper-codex copier template.
- Record decisions in docs without touching runtime tools or execution paths.

## Constraints
- No network access unless explicitly approved by the packet contract.
- Limit edits to the contract, strategy doc, and this skill folder.

## Inputs
- `control/packet/packet-001-copier-consumption.json`
- Repo structure under `.codex/`, `control/`, `docs/`, `tools/`, `ledger/`

## Outputs
- `docs/copier-consumption-strategy.md`
