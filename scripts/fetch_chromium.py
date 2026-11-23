#!/usr/bin/env python3
"""Crea o allinea il checkout Chromium al commit pinnato in versions.json."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHROMIUM_DIR = ROOT / "chromium"
SRC = CHROMIUM_DIR / "src"
VERSIONS = ROOT / "versions.json"
MIN_FREE_GB = 120

GCLIENT_TEMPLATE = """solutions = [
  {{
    "name": "src",
    "url": "https://chromium.googlesource.com/chromium/src.git",
    "managed": False,
    "custom_deps": {{}},
    "custom_vars": {{}},
  }},
]
target_os = ["win"]
"""


def load_pin() -> dict:
    data = json.loads(VERSIONS.read_text(encoding="utf-8"))
    return data["chromium"]


def run(command: list[str], cwd: Path, dry_run: bool) -> int:
    print("+", " ".join(command))
    if dry_run:
        return 0
    return subprocess.run(command, cwd=cwd, check=False).returncode


def git_head() -> str:
    if not (SRC / ".git").exists():
        return ""
    result = subprocess.run(
        ["git", "-C", str(SRC), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False)
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="salta i controlli di spazio")
    parser.add_argument("--no-hooks", action="store_true")
    args = parser.parse_args()

    pin = load_pin()
    commit = pin["commit"]
    tag = pin["tag"]

    if not args.force:
        free_gb = shutil.disk_usage(ROOT).free / (1024 ** 3)
        if free_gb < MIN_FREE_GB:
            print(f"ERRORE: {free_gb:.0f} GB liberi, servono almeno "
                  f"{MIN_FREE_GB} GB. Vedi docs/BUILD.md.", file=sys.stderr)
            return 1
        if not shutil.which("gclient"):
            print("ERRORE: gclient non nel PATH. Installa depot_tools.",
                  file=sys.stderr)
            return 1

    CHROMIUM_DIR.mkdir(parents=True, exist_ok=True)
    gclient_file = CHROMIUM_DIR / ".gclient"
    if not gclient_file.exists():
        print(f"Scrivo {gclient_file}")
        if not args.dry_run:
            gclient_file.write_text(GCLIENT_TEMPLATE, encoding="utf-8")

    if not (SRC / ".git").exists():
        code = run(
            ["gclient", "sync", "--revision", f"src@{commit}",
             "--with_branch_heads", "--with_tags"],
            CHROMIUM_DIR, args.dry_run)
        if code != 0:
            print("ERRORE: gclient sync fallita.", file=sys.stderr)
            return code
    else:
        head = git_head()
        print(f"Checkout esistente: {head[:12] or 'sconosciuto'}")
        code = run(
            ["gclient", "sync", "--revision", f"src@{commit}"],
            CHROMIUM_DIR, args.dry_run)
        if code != 0:
            return code

    if not args.dry_run:
        head = git_head()
        if head != commit:
            print(f"ERRORE: HEAD {head or '(assente)'} != commit pinnato "
                  f"{commit}. Il checkout non è quello previsto.",
                  file=sys.stderr)
            return 1
        if not args.no_hooks:
            if run(["gclient", "runhooks"], CHROMIUM_DIR, False) != 0:
                print("ERRORE: gclient runhooks fallita.", file=sys.stderr)
                return 1
        record = {
            "checked_out_at": datetime.now(timezone.utc).isoformat(),
            "tag": tag,
            "commit": commit,
            "milestone": pin["milestone"],
        }
        (CHROMIUM_DIR / ".umbrella-checkout.json").write_text(
            json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(f"Checkout verificato: {tag} ({commit[:12]})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
