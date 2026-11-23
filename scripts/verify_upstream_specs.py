#!/usr/bin/env python3
"""Verifica le specifiche contro i file upstream reali, senza clonare Chromium."""

from __future__ import annotations

import argparse
import base64
import json
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from integration.engine import apply_operations  # noqa: E402
from integration.specs import OPERATIONS  # noqa: E402

CACHE = ROOT / ".cache" / "upstream-specs"
VERSIONS = ROOT / "versions.json"
BASE = ("https://chromium.googlesource.com/chromium/src/+/refs/tags/"
        "{tag}/{path}?format=TEXT")


def unique_files() -> list[str]:
    return sorted({operation.file for operation in OPERATIONS})


def fetch(tag: str, path: str, refresh: bool) -> str:
    cached = CACHE / tag / path
    if cached.is_file() and not refresh:
        return cached.read_text(encoding="utf-8")

    url = BASE.format(tag=tag, path=path)
    request = urllib.request.Request(
        url, headers={"User-Agent": "umbrella-spec-check/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = base64.b64decode(response.read())
    except urllib.error.URLError as error:
        raise SystemExit(f"ERRORE download {path}: {error}") from error

    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(payload)
    return payload.decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true",
                        help="ignora la cache locale")
    args = parser.parse_args()

    data = json.loads(VERSIONS.read_text(encoding="utf-8"))
    tag = data["chromium"]["tag"]

    with tempfile.TemporaryDirectory(prefix="umbrella-specs-") as temporary:
        src = Path(temporary)
        for relative in unique_files():
            content = fetch(tag, relative, args.refresh)
            destination = src / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8", newline="")

        results = apply_operations(src, OPERATIONS, check=True)

    errors = [result for result in results if result.status == "error"]
    for result in results:
        marker = "!" if result.status == "error" else "="
        print(f"[{marker}] {result.file}: {result.detail}")
    print(f"\n{tag}: {len(results)} operazioni, {len(errors)} errori.")
    if errors:
        print("Le specifiche non corrispondono al tag: aggiorna "
              "integration/specs.py.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
