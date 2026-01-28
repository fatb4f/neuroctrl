# AGENTS.md (repo)

## Working agreements
- Prefer mechanical checks over narrative claims.
- Keep changes inside the allowed packet scope for the current task.
- When adding generated views (e.g., Mermaid), add a regen script and enforce regen-and-compare.

## Repo structure
- Packet contracts live under `.codex/packets/` (examples under `.codex/packets/examples/`).
- Codex skills live under `.codex/skills/`.
## Plant A updates
`.codex/` is managed as a git subtree from `fatb4f/codex-plant-a`.
```bash
git subtree pull --prefix .codex https://github.com/fatb4f/codex-plant-a.git main --squash
```
