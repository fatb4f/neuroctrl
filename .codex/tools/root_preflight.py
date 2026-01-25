#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError as e:
        return 127, "", str(e)


def git_root() -> Optional[Path]:
    rc, out, err = run(["git", "rev-parse", "--show-toplevel"])
    if rc != 0:
        return None
    return Path(out.strip())


def git_dir(repo: Path) -> Optional[Path]:
    rc, out, err = run(["git", "rev-parse", "--git-dir"], cwd=repo)
    if rc != 0:
        return None
    d = out.strip()
    return (repo / d).resolve()


def git_porcelain(repo: Path) -> List[str]:
    rc, out, err = run(["git", "status", "--porcelain"], cwd=repo)
    if rc != 0:
        return []
    return [ln.rstrip("\n") for ln in out.splitlines() if ln.strip()]


def git_symbolic_ref(repo: Path) -> Tuple[bool, str]:
    rc, out, err = run(["git", "symbolic-ref", "-q", "--short", "HEAD"], cwd=repo)
    if rc != 0:
        return False, ""
    return True, out.strip()


def git_rev_parse(repo: Path, ref: str) -> Optional[str]:
    rc, out, err = run(["git", "rev-parse", "--verify", ref], cwd=repo)
    if rc != 0:
        return None
    return out.strip()


def git_op_in_progress(gitdir: Path) -> bool:
    markers = [
        "rebase-apply",
        "rebase-merge",
        "MERGE_HEAD",
        "CHERRY_PICK_HEAD",
        "REVERT_HEAD",
        "BISECT_LOG",
        "BISECT_NAMES",
    ]
    for name in markers:
        if (gitdir / name).exists():
            return True
    return False


def safe_read_json(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not path.exists():
        return None, f"contract not found: {path}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as e:
        return None, f"failed to parse contract json: {e}"


def ensure_keys(obj: Dict[str, Any], required: List[str]) -> Optional[str]:
    missing = [k for k in required if k not in obj]
    if missing:
        return f"missing required keys: {missing}"
    return None


def ensure_no_extra(obj: Dict[str, Any], allowed: List[str]) -> Optional[str]:
    extras = [k for k in obj.keys() if k not in allowed]
    if extras:
        return f"unexpected keys: {sorted(extras)}"
    return None


def ensure_type(name: str, value: Any, typ: type) -> Optional[str]:
    if not isinstance(value, typ):
        return f"{name} must be {typ.__name__}"
    return None


def ensure_array_of_strings(name: str, value: Any) -> Optional[str]:
    if not isinstance(value, list):
        return f"{name} must be array"
    for item in value:
        if not isinstance(item, str):
            return f"{name} must contain only strings"
    return None


def validate_worktree_policy(policy: Dict[str, Any]) -> Optional[str]:
    required = ["mode", "worktree_root", "deny_if_worktree_exists", "allow_dirty_globs", "allow_untracked_globs"]
    err = ensure_keys(policy, required)
    if err:
        return f"worktree_policy: {err}"
    err = ensure_no_extra(policy, required)
    if err:
        return f"worktree_policy: {err}"
    if policy.get("mode") not in ("strict", "allow_dirty_allowlist"):
        return "worktree_policy.mode must be strict or allow_dirty_allowlist"
    err = ensure_type("worktree_policy.worktree_root", policy.get("worktree_root"), str)
    if err:
        return err
    err = ensure_type("worktree_policy.deny_if_worktree_exists", policy.get("deny_if_worktree_exists"), bool)
    if err:
        return err
    err = ensure_array_of_strings("worktree_policy.allow_dirty_globs", policy.get("allow_dirty_globs"))
    if err:
        return err
    err = ensure_array_of_strings("worktree_policy.allow_untracked_globs", policy.get("allow_untracked_globs"))
    if err:
        return err
    return None


def validate_network_policy(policy: Dict[str, Any]) -> Optional[str]:
    required = ["internet_access", "domain_allowlist_preset", "additional_domains", "allowed_http_methods"]
    err = ensure_keys(policy, required)
    if err:
        return f"network_policy: {err}"
    err = ensure_no_extra(policy, required)
    if err:
        return f"network_policy: {err}"
    if policy.get("internet_access") not in ("off", "on"):
        return "network_policy.internet_access must be off or on"
    err = ensure_type("network_policy.domain_allowlist_preset", policy.get("domain_allowlist_preset"), str)
    if err:
        return err
    err = ensure_array_of_strings("network_policy.additional_domains", policy.get("additional_domains"))
    if err:
        return err
    err = ensure_array_of_strings("network_policy.allowed_http_methods", policy.get("allowed_http_methods"))
    if err:
        return err
    return None


def validate_evidence(evidence: Dict[str, Any]) -> Optional[str]:
    required = ["out_dir", "include_git_diff_patch"]
    err = ensure_keys(evidence, required)
    if err:
        return f"evidence: {err}"
    err = ensure_no_extra(evidence, required)
    if err:
        return f"evidence: {err}"
    err = ensure_type("evidence.out_dir", evidence.get("out_dir"), str)
    if err:
        return err
    err = ensure_type("evidence.include_git_diff_patch", evidence.get("include_git_diff_patch"), bool)
    if err:
        return err
    return None


def validate_contract(contract: Dict[str, Any]) -> Optional[str]:
    required = [
        "packet_id",
        "area",
        "repo",
        "base_ref",
        "branch",
        "github_ops_required",
        "allowed_paths",
        "forbidden_outputs",
        "worktree_policy",
        "network_policy",
        "evidence",
    ]
    err = ensure_keys(contract, required)
    if err:
        return err

    allowed_keys = [
        "packet_id",
        "area",
        "repo",
        "base_ref",
        "branch",
        "github_ops_required",
        "allowed_paths",
        "forbidden_outputs",
        "worktree_policy",
        "network_policy",
        "run",
        "budgets",
        "evidence",
        "evidence_required",
    ]
    err = ensure_no_extra(contract, allowed_keys)
    if err:
        return err

    for key in ("packet_id", "area", "repo", "base_ref", "branch"):
        err = ensure_type(key, contract.get(key), str)
        if err:
            return err
    err = ensure_type("github_ops_required", contract.get("github_ops_required"), bool)
    if err:
        return err

    err = ensure_array_of_strings("allowed_paths", contract.get("allowed_paths"))
    if err:
        return err
    if not contract.get("allowed_paths"):
        return "allowed_paths must not be empty"
    err = ensure_array_of_strings("forbidden_outputs", contract.get("forbidden_outputs"))
    if err:
        return err

    err = validate_worktree_policy(contract.get("worktree_policy", {}))
    if err:
        return err

    err = validate_network_policy(contract.get("network_policy", {}))
    if err:
        return err

    err = validate_evidence(contract.get("evidence", {}))
    if err:
        return err

    if "evidence_required" in contract:
        err = ensure_array_of_strings("evidence_required", contract.get("evidence_required"))
        if err:
            return err

    return None


@dataclass
class Decision:
    allow: bool = True
    deny_code: Optional[str] = None
    message: Optional[str] = None

    def deny(self, code: str, message: str) -> None:
        if self.allow:
            self.allow = False
            self.deny_code = code
            self.message = message


def default_evidence_path(contract: Optional[Dict[str, Any]]) -> Path:
    out_dir = ".codex/out"
    packet_id = "unknown"
    if contract:
        packet_id = str(contract.get("packet_id") or packet_id)
        evidence = contract.get("evidence") or {}
        out_dir = str(evidence.get("out_dir") or out_dir)
    return Path(out_dir) / packet_id / "root_preflight.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Root preflight (S0) gate.")
    parser.add_argument("--contract", required=True, help="Path to packet contract JSON.")
    parser.add_argument("--evidence-out", help="Override evidence output path.")
    args = parser.parse_args()

    repo_root = git_root()
    decision = Decision()

    contract_path = Path(args.contract)
    contract, contract_err = safe_read_json(contract_path)

    evidence_path = Path(args.evidence_out) if args.evidence_out else default_evidence_path(contract)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)

    base_ref = None
    github_ops_required = False
    worktree_root = ".codex/.worktrees"

    if contract is None:
        decision.deny("CONTRACT_INVALID", contract_err or "contract parse failed")
    else:
        base_ref = contract.get("base_ref")
        github_ops_required = bool(contract.get("github_ops_required", False))
        policy = contract.get("worktree_policy") or {}
        worktree_root = str(policy.get("worktree_root") or worktree_root)
        if not isinstance(base_ref, str) or not base_ref.strip():
            decision.deny("BASE_REF_MISSING", "base_ref missing or empty")

    if repo_root is None:
        decision.deny("ENVELOPE_UNAVAILABLE", "not a git repository")
    else:
        cwd = Path.cwd().resolve()
        if cwd != repo_root.resolve():
            decision.deny("ENVELOPE_UNAVAILABLE", "not running from repo root")
        if ".worktrees" in cwd.parts:
            decision.deny("ENVELOPE_UNAVAILABLE", "preflight must run from repo root (not inside .codex/.worktrees)")

    if decision.allow and repo_root:
        if git_porcelain(repo_root):
            decision.deny("DIRTY_ROOT_PRE", "root working tree not clean")

    if decision.allow and repo_root:
        gdir = git_dir(repo_root)
        if gdir and git_op_in_progress(gdir):
            decision.deny("GIT_OP_IN_PROGRESS", "git operation in progress in root")

    head_ok = False
    head_ref = ""
    if decision.allow and repo_root:
        head_ok, head_ref = git_symbolic_ref(repo_root)
        if not head_ok:
            decision.deny("HEAD_DETACHED_PRE", "HEAD is detached in root")

    if decision.allow and repo_root and base_ref:
        if git_rev_parse(repo_root, base_ref) is None:
            decision.deny("BASE_REF_MISSING", f"base_ref not resolvable: {base_ref}")

    if decision.allow and contract is not None:
        err = validate_contract(contract)
        if err:
            decision.deny("CONTRACT_INVALID", err)

    if decision.allow:
        if shutil.which("git") is None:
            decision.deny("TOOLS_MISSING", "git not available in PATH")
        if not sys.executable or not Path(sys.executable).exists():
            decision.deny("TOOLS_MISSING", "python interpreter not available")

    if decision.allow and repo_root:
        if not os.access(repo_root, os.W_OK):
            decision.deny("ENVELOPE_UNAVAILABLE", "repo root is not writable")
        wt_root = repo_root / worktree_root
        if wt_root.exists() and not os.access(wt_root, os.W_OK):
            decision.deny("ENVELOPE_UNAVAILABLE", "worktree root is not writable")
        usage = shutil.disk_usage(repo_root)
        if usage.free <= 0:
            decision.deny("ENVELOPE_UNAVAILABLE", "no free disk space available")

    probes: Dict[str, Dict[str, Any]] = {}
    tx_mode = "offline"
    if repo_root:
        if shutil.which("gh") is None:
            probes["gh_auth_status"] = {"rc": 127, "stdout": "", "stderr": "gh not found"}
            probes["gh_pr_list"] = {"rc": 127, "stdout": "", "stderr": "gh not found"}
            rc = 127
            rc2 = 127
        else:
            rc, out, err = run(["gh", "auth", "status"], cwd=repo_root)
            probes["gh_auth_status"] = {"rc": rc, "stdout": out, "stderr": err}
            rc2, out2, err2 = run(["gh", "pr", "list", "--limit", "1"], cwd=repo_root)
            probes["gh_pr_list"] = {"rc": rc2, "stdout": out2, "stderr": err2}
        rc3, out3, err3 = run(["git", "ls-remote", "origin", "HEAD"], cwd=repo_root)
        probes["git_ls_remote"] = {"rc": rc3, "stdout": out3, "stderr": err3}
        if rc == 0 and rc2 == 0:
            tx_mode = "online"

        if decision.allow and github_ops_required:
            if rc != 0 or rc2 != 0:
                decision.deny("GITHUB_UNAVAILABLE", "GitHub auth/PR API unavailable")

    evidence = {
        "stage": "S0",
        "timestamp_utc": utc_now(),
        "repo_root": str(repo_root) if repo_root else None,
        "base_ref": base_ref,
        "head_ref": head_ref if head_ok else "DETACHED",
        "github_ops_required": github_ops_required,
        "tx_mode": tx_mode,
        "probes": probes,
        "decision": "ALLOW" if decision.allow else "DENY",
        "deny_code": decision.deny_code,
        "message": decision.message,
    }
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return 0 if decision.allow else 2


if __name__ == "__main__":
    raise SystemExit(main())
