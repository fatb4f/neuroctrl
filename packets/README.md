# Packets

Packets are **mechanical, auditable units of work** executed through Codex skills.

## Concepts
- **Contract**: a JSON file that declares intent, boundaries, and allowed moves.
- **Worktree**: each packet executes inside an isolated git worktree under `.codex/.worktrees/<packet_id>`.
- **Evidence**: each run emits immutable artifacts under `.codex/out/<packet_id>/`.

## Required invariants
- No execution on a dirty base repo (unless explicitly allowed by `worktree_policy`).
- Packet execution occurs in an isolated worktree.
- Evidence is always emitted (manifest + hashes).

## Files
- `packet_contract.template.md`: canonical contract template to copy into a packet contract file.

## Typical usage
1) Create contract under `packet/examples/<packet_id>.json`.
2) Run `packet-runner` with the contract path.
3) Review evidence under `.codex/out/<packet_id>/`.
