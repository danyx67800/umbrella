#!/usr/bin/env python3
"""Verifica, applica o annulla l'integrazione Umbrella nel checkout Chromium."""

from __future__ import annotations

import argparse
import dataclasses
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from integration.engine import apply_operations, describe_operations  # noqa: E402
from integration.specs import OPERATIONS  # noqa: E402

DEFAULT_SRC = ROOT / "chromium" / "src"
BACKUP_DIR = ROOT / "chromium" / ".umbrella-integration-backup"


def _status_line(result) -> str:
    icons = {
        "applied": "+",
        "ok": "=",
        "skipped": "·",
        "error": "!",
    }
    return f"[{icons.get(result.status, '?')}] {result.file}: {result.detail}"


def _unique_files() -> list[str]:
    return sorted({operation.file for operation in OPERATIONS})


def _backup(src: Path) -> int:
    count = 0
    for relative in _unique_files():
        source = src / relative
        if not source.is_file():
            continue
        target = BACKUP_DIR / relative
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        count += 1
    return count


def _revert() -> int:
    if not BACKUP_DIR.is_dir():
        print("Nessun backup di integrazione presente.")
        return 0
    restored = 0
    for backup in BACKUP_DIR.rglob("*"):
        if not backup.is_file():
            continue
        relative = backup.relative_to(BACKUP_DIR)
        source = ROOT / "chromium" / "src" / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup, source)
        restored += 1
    shutil.rmtree(BACKUP_DIR)
    print(f"Ripristinati {restored} file upstream.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC,
                        help="radice del checkout Chromium (default: chromium/src)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="verifica gli anchor senza scrivere")
    mode.add_argument("--apply", action="store_true",
                      help="applica le modifiche con backup")
    mode.add_argument("--revert", action="store_true",
                      help="ripristina i file dal backup")
    mode.add_argument("--list", action="store_true",
                      help="elenca le operazioni")
    parser.add_argument("--json", action="store_true", help="output JSON")
    args = parser.parse_args()

    if args.list:
        for line in describe_operations(OPERATIONS):
            print(line)
        return 0

    if args.revert:
        return _revert()

    src: Path = args.src.resolve()
    if not src.is_dir():
        print(f"ERRORE: checkout non trovato: {src}", file=sys.stderr)
        print("Esegui prima: python scripts/fetch_chromium.py", file=sys.stderr)
        return 1

    if args.apply:
        _backup(src)

    results = apply_operations(src, OPERATIONS, check=args.check)
    errors = [result for result in results if result.status == "error"]

    if args.json:
        print(json.dumps([dataclasses.asdict(result) for result in results],
                         indent=2, ensure_ascii=False))
    else:
        print(f"{'CHECK' if args.check else 'APPLY'} — {len(results)} operazioni, "
              f"{len(errors)} errori")
        for result in results:
            print(_status_line(result))

    if errors:
        print("\nIntegrazione NON valida: aggiorna integration/specs.py "
              "leggendo il nuovo sorgente upstream.", file=sys.stderr)
        return 1

    if args.check:
        print("\nTutti gli anchor sono presenti una sola volta.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
