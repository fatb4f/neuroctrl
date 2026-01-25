#!/usr/bin/env python3
"""Packet runner (canonical).

Responsibilities:
- provision isolated git worktree for the packet
- execute regen/test/commands (if configured)
- always emit Packet-002 evidence bundle via tools/evidence/collect_packet_evidence.py

Notes:
- stdlib only
- evidence is written to .codex/out/<packet_id>/
"""

from __future__ import annotations

import datetime as _dt
import json
import pathlib
import platform
import subprocess
import sys
from typing import Any, Dict, List, Tuple

RUNNER_VERSION = "0.1.1"  # Packet-002
PLANT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def sh(cmd: List[str], cwd: str | None = None) -> Tuple[int, str, str]:
    p = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, err = p.communicate()
    return p.returncode, out, err


def die(msg: str, code: int = 2) -> None:
    raise SystemExit(f"{msg.rstrip()}\n")


def load_json(path: str) -> Dict[str, Any]:
    p = pathlib.Path(path)
    if not p.exists():
        raise SystemExit(f"contract not found: {path}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit(f"failed to parse contract json: {e}")


def require(d: Dict[str, Any], k: str, typ: type | tuple[type, ...]) -> Any:
    if k not in d:
        raise SystemExit(f"missing required key: {k}")
    v = d[k]
    if not isinstance(v, typ):
        raise SystemExit(f"invalid type for {k}: expected {typ}, got {type(v)}")
    return v


def validate_network_policy(policy: Dict[str, Any]) -> None:
    required = [
        ("internet_access", str),
        ("domain_allowlist_preset", str),
        ("additional_domains", list),
        ("allowed_http_methods", list),
    ]
    for key, typ in required:
        if key not in policy:
            raise SystemExit(f"network_policy missing key: {key}")
        if not isinstance(policy[key], typ):
            raise SystemExit(f"network_policy.{key} must be {typ.__name__}")


def git_porcelain(cwd: str | None = None) -> List[str]:
    rc, out, err = sh(["git", "status", "--porcelain"], cwd=cwd)
    if rc != 0:
        raise SystemExit(f"git status failed: {err.strip()}")
    return [ln.rstrip("\n") for ln in out.splitlines() if ln.strip()]


def git_rev_parse(ref: str, cwd: str | None = None) -> str:
    rc, out, err = sh(["git", "rev-parse", "--verify", ref], cwd=cwd)
    if rc != 0:
        raise SystemExit(f"git rev-parse failed for {ref}: {err.strip()}")
    return out.strip()




def write_text(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: pathlib.Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def gate_evidence_path(out_dir: str, packet_id: str, name: str) -> pathlib.Path:
    return pathlib.Path(out_dir) / packet_id / f"{name}.json"


def run_gate(script: pathlib.Path, contract_path: str, evidence_path: pathlib.Path) -> int:
    argv = [sys.executable, str(script), "--contract", contract_path, "--evidence-out", str(evidence_path)]
    p = subprocess.run(argv, check=False)
    return p.returncode


def run_commands(run_cfg: Dict[str, Any], cwd: str, out_log: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Runs regen_cmd, test_cmd, then run.commands (in that order)."""

    cmds: List[Tuple[str, str]] = []  # (kind, cmd)
    regen = (run_cfg.get("regen_cmd") or "").strip()
    test = (run_cfg.get("test_cmd") or "").strip()
    extra = run_cfg.get("commands") or []

    if regen:
        cmds.append(("regen", regen))
    if test:
        cmds.append(("test", test))
    if isinstance(extra, list):
        cmds.extend([("cmd", str(x)) for x in extra if str(x).strip()])

    results: List[Dict[str, Any]] = []
    test_rc: int | None = None
    tests_output: str | None = None

    for kind, c in cmds:
        out_log.append(f"$ {c}")
        rc, out, err = sh(["bash", "-lc", c], cwd=cwd)
        results.append({"kind": kind, "cmd": c, "rc": rc})
        if out.strip():
            out_log.append(out.rstrip())
        if err.strip():
            out_log.append(err.rstrip())

        if kind == "test":
            test_rc = rc
            tests_output = (out or "") + ("\n" if out and not out.endswith("\n") else "") + (err or "")

        if rc != 0:
            break

    meta = {"test_rc": test_rc, "tests_output": tests_output}
    return results, meta


def collect_packet_evidence(contract_path: str, meta_path: pathlib.Path | None) -> None:
    collector = PLANT_ROOT / "tools" / "evidence" / "collect_packet_evidence.py"
    argv = [sys.executable, str(collector), "--contract", contract_path]
    if meta_path is not None:
        argv += ["--meta", str(meta_path)]
    subprocess.run(argv, check=False)


def required_evidence_missing(out_base: pathlib.Path) -> List[str]:
    required_files = [
        out_base / "evidence.json",
        out_base / "evidence.md",
        out_base / "manifest.json",
        out_base / "manifest.sha256",
        out_base / "raw" / "head_before.txt",
        out_base / "raw" / "status_before.txt",
        out_base / "raw" / "head_after.txt",
        out_base / "raw" / "status_after.txt",
        out_base / "raw" / "diff_name_only.txt",
        out_base / "raw" / "diffstat.txt",
    ]
    return [str(p) for p in required_files if not p.exists()]


def read_json(path: pathlib.Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write("usage: .codex/tools/run_packet.py <contract_path>\n")
        return 2

    contract_path = argv[1]
    contract = load_json(contract_path)

    packet_id = require(contract, "packet_id", str)
    base_ref = require(contract, "base_ref", str)
    branch = require(contract, "branch", str)
    github_ops_required = require(contract, "github_ops_required", bool)
    network_policy = require(contract, "network_policy", dict)
    validate_network_policy(network_policy)
    evidence_cfg = require(contract, "evidence", dict)

    out_dir = str(evidence_cfg.get("out_dir", str(PLANT_ROOT / "out")))
    out_base = pathlib.Path(out_dir) / packet_id
    raw_dir = out_base / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    run_log: List[str] = []
    run_log.append(f"packet_id={packet_id}")
    run_log.append(f"contract_path={contract_path}")
    run_log.append(f"runner_version={RUNNER_VERSION}")
    run_log.append(f"utc_start={_dt.datetime.now(_dt.timezone.utc).isoformat().replace('+00:00', 'Z')}")
    run_log.append(f"network_internet_access={network_policy.get('internet_access')}")

    decision = "DENY"
    reasons: List[str] = []
    final_status = "FAIL"

    meta_path = raw_dir / "meta.json"

    wt_path: str | None = None
    base_sha: str | None = None
    test_rc: int | None = None
    tests_output: str | None = None

    try:
        preflight_path = gate_evidence_path(out_dir, packet_id, "root_preflight")
        g0_path = gate_evidence_path(out_dir, packet_id, "g0_enter_work")

        rc = run_gate(PLANT_ROOT / "tools" / "root_preflight.py", contract_path, preflight_path)
        if rc != 0:
            raise SystemExit("root preflight denied")

        rc = run_gate(PLANT_ROOT / "tools" / "g0_enter_work.py", contract_path, g0_path)
        if rc != 0:
            raise SystemExit("G0 enter work denied")

        g0_evidence = read_json(g0_path)
        wt_path = g0_evidence.get("worktree_path")
        base_sha = g0_evidence.get("base_sha") or git_rev_parse(base_ref)
        if not wt_path:
            raise SystemExit("worktree_path not set by G0")

        # Pre-run snapshot inside worktree
        head_before = git_rev_parse("HEAD", cwd=wt_path)
        status_before = git_porcelain(cwd=wt_path)
        write_text(raw_dir / "head_before.txt", head_before + "\n")
        write_text(raw_dir / "status_before.txt", "\n".join(status_before) + ("\n" if status_before else ""))

        run_cfg = contract.get("run", {})
        cmd_results, run_meta = run_commands(run_cfg, cwd=wt_path, out_log=run_log)

        test_rc = run_meta.get("test_rc")
        tests_output = run_meta.get("tests_output")
        if tests_output is not None:
            write_text(raw_dir / "tests.txt", tests_output)

        # Post-run snapshot inside worktree
        head_after = git_rev_parse("HEAD", cwd=wt_path)
        status_after = git_porcelain(cwd=wt_path)
        write_text(raw_dir / "head_after.txt", head_after + "\n")
        write_text(raw_dir / "status_after.txt", "\n".join(status_after) + ("\n" if status_after else ""))

        final_rc = int(cmd_results[-1]["rc"]) if cmd_results else 0
        decision = "ALLOW" if final_rc == 0 else "DENY"

        # Keep a compact machine-readable run record (the collector handles canonical evidence.json)
        write_json(raw_dir / "run_commands.json", {"commands": cmd_results, "final_rc": final_rc})

    except SystemExit as e:
        reasons.append(str(e).strip())
    except Exception as e:
        reasons.append(f"unhandled_error: {e}")
    finally:
        run_log.append(f"utc_end={_dt.datetime.now(_dt.timezone.utc).isoformat().replace('+00:00', 'Z')}")
        write_text(raw_dir / "runner.log", "\n".join(run_log) + "\n")

        meta = {
            "runner_version": RUNNER_VERSION,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "repo_root": str(pathlib.Path.cwd()),
            "packet_id": packet_id,
            "base_ref": base_ref,
            "base_sha": base_sha,
            "branch": branch,
            "github_ops_required": github_ops_required,
            "network_policy": network_policy,
            "worktree_path": wt_path,
            "decision": decision,
            "reasons": reasons,
            "test_rc": test_rc,
            "tests_output": tests_output,
            "resolved": {
                "base_ref": base_ref,
                "base_sha": base_sha,
                "branch": branch,
                "worktree_path": wt_path,
            },
        }
        write_json(meta_path, meta)

        # Always run the Packet-002 collector (even on DENY)
        collect_packet_evidence(contract_path=contract_path, meta_path=meta_path)

    missing = required_evidence_missing(out_base)
    evidence_decision = None
    evidence_path = out_base / "evidence.json"
    if evidence_path.exists():
        try:
            evidence = read_json(evidence_path)
            evidence_decision = evidence.get("decision")
        except Exception as e:
            missing.append(f"{evidence_path}: {e}")

    if missing:
        decision = "DENY"
        reasons.append("missing_evidence_outputs")

    if evidence_decision and evidence_decision != "ALLOW":
        decision = "DENY"
        reasons.append("evidence_denied")

    final_status = "PASS" if decision == "ALLOW" else "DENY"
    if any(r.startswith("unhandled_error") for r in reasons):
        final_status = "FAIL"

    meta["decision"] = decision
    meta["reasons"] = reasons
    meta["final_status"] = final_status
    meta["evidence_decision"] = evidence_decision
    meta["missing_evidence_outputs"] = missing
    write_json(meta_path, meta)

    return 0 if final_status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
