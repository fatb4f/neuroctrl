# control/packet

Controller-side source of truth for packet contracts and their schemas.

- `packet_contract.schema.json` defines the machine-readable packet contract format.
- `examples/` contains sample contracts.

Convention:
- Store Markdown contracts as `control/packet/<packet_id>.md`
- Optionally store machine-readable contracts as `control/packet/<packet_id>.json` for validation.
