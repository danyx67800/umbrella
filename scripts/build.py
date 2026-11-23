#!/usr/bin/env python3
"""Configura e compila Umbrella con GN + Ninja (autoninja)."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "chromium" / "src"
ARGS_DIR = ROOT / "gn" / "args"

INTEGRATION_MARKERS = [
    SRC / "chrome/browser/chrome_browser_main.cc",
    SRC / "chrome/browser/search/search.cc",
]


def fail(message: str) -> int:
    print(f"ERRORE: {message}", file=sys.stderr)
    return 1


def verify_ready() -> str | None:
    if not SRC.is_dir():
        return "checkout assente: esegui scripts/fetch_chromium.py"
    if not (SRC / "chrome/browser/umbrella").is_dir():
        return "overlay assente: esegui scripts/link_overlay.py"
    for path in INTEGRATION_MARKERS:
        if not path.is_file():
            return f"file upstream mancante: {path}"
        text = path.read_text(encoding="utf-8", errors="replace")
        if "umbrella" not in text.lower():
            return ("integrazione non applicata: esegui "
                    "scripts/integrate.py --apply")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--target", default="chrome")
    parser.add_argument("--jobs", type=int, default=0)
    parser.add_argument("--extra-args", default="",
                        help="righe aggiuntive per args.gn")
    args = parser.parse_args()

    if args.debug and args.release:
        return fail("scegli --debug oppure --release")
    debug = args.debug

    problem = verify_ready()
    if problem:
        return fail(problem)

    for tool in ("gn", "autoninja"):
        if not shutil.which(tool):
            return fail(f"{tool} non nel PATH: installa depot_tools")

    template = ARGS_DIR / ("umbrella_debug.gn" if debug else "umbrella.gn")
    if not template.is_file():
        return fail(f"template GN mancante: {template}")

    out_name = "UmbrellaDebug" if debug else "Umbrella"
    out_dir = SRC / "out" / out_name
    out_dir.mkdir(parents=True, exist_ok=True)

    content = template.read_text(encoding="utf-8").rstrip() + "\n"
    if args.extra_args.strip():
        content += "\n# Extra da riga di comando\n" + args.extra_args.strip() + "\n"
    (out_dir / "args.gn").write_text(content, encoding="utf-8")

    print(f"gn gen out/{out_name}")
    if subprocess.run(["gn", "gen", f"out/{out_name}"], cwd=SRC,
                      check=False).returncode != 0:
        return fail("gn gen fallita")

    command = ["autoninja", "-C", f"out/{out_name}"]
    if args.jobs > 0:
        command.append(f"-j{args.jobs}")
    command.append(args.target)

    print("+", " ".join(command))
    if subprocess.run(command, cwd=SRC, check=False).returncode != 0:
        return fail("compilazione fallita")

    exe = out_dir / "chrome.exe"
    if exe.is_file():
        print(f"\nBuild completata: {exe} ({exe.stat().st_size / 1024 / 1024:.1f} MB)")
    else:
        print("\nBuild completata; eseguibile non trovato al percorso atteso.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
