# Packet: <packet-id> — <title>

**Domain:** <engineering|operations>  
**Area:** <content-gen|pipeline-sre|engineering|ops>  
**Status:** DRAFT

## Purpose
<one paragraph>

## Scope boundary (illegal moves)
- <illegal move 1>
- <illegal move 2>

## Inputs
- Files/dirs assumed to exist:
  - `<path>`
- External requirements (if any):
  - `<requirement>`

## Outputs (exact paths)
- `<path>`
- `<path>`

## End-state predicate (mechanical)
- Command(s) to run:
  - `...`
- Expected results:
  - `...`

## Evidence artifacts (paths)
- `<path>`
- `<path>`

## Failure modes / rollback
- <what can go wrong>
- <how to revert safely>

## Forbidden actions
- Network access (unless explicitly allowed)
- Large refactors outside scope
- Changing policy/contracts without updating evidence
