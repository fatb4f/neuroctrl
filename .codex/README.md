# Codex Plant Surface

This directory is the isolated Codex "plant" surface. It is intended to be copied into downstream repos
as a single folder with no template-managed files outside `.codex/`.

## Install (downstream)
```bash
copier copy <TEMPLATE_URL> .codex
```

## Run a packet
```bash
bash .codex/skills/packet-runner/scripts/run_packet.sh .codex/packet/examples/packet-000-foundation.json
```

## Evidence output
Evidence bundles are written under:
```
.codex/out/<packet_id>/
```
