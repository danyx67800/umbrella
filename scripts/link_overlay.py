#!/usr/bin/env python3
"""Installa, verifica o rimuove l'overlay Umbrella nel checkout Chromium."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHROMIUM_DIR = ROOT / "chromium"
DEFAULT_SRC = CHROMIUM_DIR / "src"
MANIFEST = CHROMIUM_DIR / ".umbrella-overlay.json"

MAPPINGS = [
    ("umbrella/browser", "chrome/browser/umbrella"),
    ("umbrella/common", "chrome/browser/umbrella/common"),
    ("umbrella/resources", "chrome/browser/resources/umbrella"),
]

IGNORED_SUFFIXES = {".pyc", ".pyo"}
IGNORED_NAMES = {".DS_Store", "Thumbs.db"}


def _iter_files(directory: Path):
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        if path.name in IGNORED_NAMES or path.suffix in IGNORED_SUFFIXES:
            continue
        yield path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest() -> dict:
    if not MANIFEST.is_file():
        return {"files": {}}
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"files": {}}


def _collect(src: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for source_dir, destination in MAPPINGS:
        base = ROOT / source_dir
        if not base.is_dir():
            raise SystemExit(f"ERRORE: directory overlay mancante: {base}")
        for path in _iter_files(base):
            relative = path.relative_to(base).as_posix()
            files[f"{destination}/{relative}"] = path
    return files


def cmd_install(src: Path, force: bool) -> int:
    if not src.is_dir():
        raise SystemExit(f"ERRORE: checkout non trovato: {src}")
    sources = _collect(src)
    previous = _load_manifest().get("files", {})
    installed = 0
    updated = 0

    for relative, source in sources.items():
        destination = src / relative
        new_hash = _sha256(source)
        if destination.exists():
            old_hash = _sha256(destination)
            if old_hash == new_hash:
                continue
            if relative not in previous and not force:
                raise SystemExit(
                    f"ERRORE: {relative} esiste nel checkout e non proviene "
                    "dall'overlay. Usa --force solo se sei sicuro.")
            updated += 1
        else:
            installed += 1
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    removed = 0
    for relative in sorted(set(previous) - set(sources)):
        stale = src / relative
        if stale.is_file():
            stale.unlink()
            removed += 1

    manifest = {
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(ROOT),
        "files": {relative: _sha256(path) for relative, path in sources.items()},
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Overlay: {installed} nuovi, {updated} aggiornati, {removed} rimossi.")
    print(f"Manifest: {MANIFEST}")
    return 0


def cmd_check(src: Path) -> int:
    sources = _collect(src)
    manifest = _load_manifest().get("files", {})
    problems: list[str] = []

    for relative, source in sources.items():
        destination = src / relative
        if not destination.is_file():
            problems.append(f"mancante: {relative}")
        elif _sha256(destination) != _sha256(source):
            problems.append(f"diverso: {relative}")
    for relative in sorted(set(manifest) - set(sources)):
        problems.append(f"obsoleto: {relative}")

    if problems:
        print("Overlay NON allineato:")
        for problem in problems:
            print(f"  - {problem}")
        print("Esegui: python scripts/link_overlay.py")
        return 1

    print(f"Overlay allineato ({len(sources)} file).")
    return 0


def cmd_clean(src: Path) -> int:
    manifest = _load_manifest().get("files", {})
    removed = 0
    for relative in sorted(manifest, reverse=True):
        path = src / relative
        if path.is_file():
            path.unlink()
            removed += 1
    for _, destination in MAPPINGS:
        directory = src / destination
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
    if MANIFEST.exists():
        MANIFEST.unlink()
    print(f"Rimossi {removed} file dell'overlay.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--clean", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    src = args.src.resolve()
    if args.check:
        return cmd_check(src)
    if args.clean:
        return cmd_clean(src)
    return cmd_install(src, args.force)


if __name__ == "__main__":
    raise SystemExit(main())
