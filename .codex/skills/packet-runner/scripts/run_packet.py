#!/usr/bin/env python3
"""Codex skill entrypoint wrapper.

Delegates to the canonical runner:
  python .codex/tools/run_packet.py <contract_path>
"""

from __future__ import annotations

import pathlib
import subprocess
import sys


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write("usage: run_packet.py <contract_path>\n")
        return 2
    contract_path = argv[1]
    plant_root = pathlib.Path(__file__).resolve().parents[3]
    runner = plant_root / "tools" / "run_packet.py"
    p = subprocess.run([sys.executable, str(runner), contract_path])
    return int(p.returncode)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
