# Copier Consumption Strategy (neuroctrl)

## Purpose
Adopt the `cper-codex` copier template into the live neuroctrl repository with controlled, auditable updates.

## Template source
- Template repo: `https://github.com/fatb4f/cper-codex`
- Pin a specific ref (tag or commit) in `.copier-answers.yml` before adoption.

## Managed scope
Treat these paths as template-managed after adoption:
- `.codex/`
- `control/`
- `docs/`
- `tools/`
- `ledger/`
- `README.md`
- `AGENTS.md`
- `.gitignore`
- `TEMPLATE_VERSION`

All other paths are local-only unless explicitly added to the template scope.

## Local overrides (initial)
- If a managed path must diverge, document the reason in `docs/copier-consumption-strategy.md` and keep a diff in review for each update.
- Avoid adding new managed paths without a deliberate decision recorded in this document.

## Adoption workflow (live repo)
1. Render the template into a temp directory.
2. Diff the temp render against the live repo to identify managed vs local-only paths.
3. Resolve conflicts by deciding which live files are local overrides vs template-owned.
4. Create or update `.copier-answers.yml` with the pinned template ref and repo-specific values.
5. Apply the template to the live repo (overwrite managed paths only).
6. Re-run diff checks and confirm only managed paths changed.

## Verification (mechanical checks)
- `test -f .copier-answers.yml`
- `rg --files -g '!*'` to list files and verify changes are limited to managed paths.

## Update policy
- Updates occur only via `copier update` from the pinned template ref.
- Each update must be reviewed by diffing managed paths and accepting only intended changes.
- Do not accept changes outside the managed scope without an explicit decision.

## Gate checks
- `.copier-answers.yml` exists after adoption.
- Managed paths match the rendered template (or documented local overrides).
- No changes appear outside the managed scope.
