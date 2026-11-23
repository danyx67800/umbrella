#!/usr/bin/env python3
"""Pubblica una release Umbrella con gh, solo con artefatti verificati."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = ROOT / "VERSION"
VERSIONS = ROOT / "versions.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str]) -> int:
    print("+", " ".join(command))
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--artifacts", nargs="+", type=Path, required=True)
    parser.add_argument("--notes", type=Path)
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--confirm", action="store_true",
                        help="conferma esplicita della pubblicazione")
    args = parser.parse_args()

    if not args.confirm:
        print("ERRORE: la pubblicazione richiede --confirm.", file=sys.stderr)
        return 1
    if subprocess.run(["gh", "auth", "status"], check=False).returncode != 0:
        print("ERRORE: gh non autenticato. Esegui gh auth login.",
              file=sys.stderr)
        return 1

    version = VERSION.read_text(encoding="utf-8").strip()
    data = json.loads(VERSIONS.read_text(encoding="utf-8"))
    if data["version"] != version:
        print("ERRORE: VERSION e versions.json divergono.", file=sys.stderr)
        return 1
    if not args.tag.endswith(version):
        print(f"ATTENZIONE: il tag {args.tag} non contiene {version}.",
              file=sys.stderr)

    for artifact in args.artifacts:
        if not artifact.is_file():
            print(f"ERRORE: artefatto assente: {artifact}", file=sys.stderr)
            return 1
        print(f"{sha256(artifact)}  {artifact.name}")

    checksum_file = ROOT / "dist" / f"SHA256SUMS-{args.tag}.txt"
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    checksum_file.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in args.artifacts),
        encoding="ascii")

    if run(["gh", "release", "view", args.tag]) == 0:
        print(f"ERRORE: la release {args.tag} esiste già.", file=sys.stderr)
        return 1

    command = ["gh", "release", "create", args.tag,
               *[str(path) for path in args.artifacts],
               str(checksum_file),
               "--title", f"Umbrella {version}"]
    if args.notes:
        command.extend(["--notes-file", str(args.notes)])
    else:
        command.extend(["--notes", f"Release Umbrella {version}"])
    if args.draft:
        command.append("--draft")
    return run(command)


if __name__ == "__main__":
    raise SystemExit(main())
