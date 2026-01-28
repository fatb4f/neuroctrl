# Codex Plant Surface

This directory is the isolated Codex "plant" surface (Plant A). It is intended to be
integrated into downstream repos as a single folder with no template-managed files outside `.codex/`.

## Plant A vs Plant B
- **Plant A (this repo):** shared Codex execution surface used across projects
  (`.codex/` tooling, packets, skills, evidence layout). It is repo-agnostic.
- **Plant B (project-specific):** domain logic, schemas, policies, and tools that live
  in the project repo outside `.codex/` (e.g., `control/`, `tools/`, `docs/`).

## Install/update (downstream)
Plant A is consumed as a git subtree under `.codex/`:
```bash
git subtree add --prefix .codex https://github.com/fatb4f/codex-plant-a.git main --squash
git subtree pull --prefix .codex https://github.com/fatb4f/codex-plant-a.git main --squash
```

## Run a packet
```bash
bash .codex/skills/packet-runner/scripts/run_packet.sh .codex/packets/examples/packet-000-foundation.json
```

## Evidence output
Evidence bundles are written under:
```
.codex/out/<packet_id>/
```
