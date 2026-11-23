#!/usr/bin/env python3
"""Verifica i requisiti della macchina prima di una build Chromium."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ROOT / "versions.json"
MIN_FREE_GB = 120
WARN_FREE_GB = 160


@dataclass
class Check:
    name: str
    ok: bool
    blocking: bool
    detail: str


def _program_files_x86() -> Path:
    return Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))


def check_versions() -> Check:
    try:
        data = json.loads(VERSIONS.read_text(encoding="utf-8"))
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        chromium = data["chromium"]
        if data["version"] != version:
            return Check("versions", False, True,
                         f"VERSION={version} != versions.json={data['version']}")
        return Check("versions", True, False,
                     f"Umbrella {version} / Chromium {chromium['tag']}")
    except (OSError, KeyError, json.JSONDecodeError) as error:
        return Check("versions", False, True, f"errore: {error}")


def check_python() -> Check:
    version = sys.version_info
    ok = version >= (3, 11)
    return Check("python", ok, True,
                 f"{version.major}.{version.minor}.{version.micro}")


def check_tool(name: str, args: list[str] | None = None) -> Check:
    path = shutil.which(name)
    if not path:
        return Check(name, False, True, "non trovato nel PATH")
    if args:
        try:
            output = subprocess.run(
                [path, *args], capture_output=True, text=True, timeout=20,
                check=False)
            detail = (output.stdout or output.stderr).strip().splitlines()
            return Check(name, True, False, detail[0] if detail else path)
        except (OSError, subprocess.SubprocessError) as error:
            return Check(name, False, True, str(error))
    return Check(name, True, False, path)


def check_gh_auth() -> Check:
    path = shutil.which("gh")
    if not path:
        return Check("gh auth", False, True, "gh non installato")
    result = subprocess.run(
        [path, "auth", "status"], capture_output=True, text=True,
        timeout=30, check=False)
    ok = result.returncode == 0
    # Non bloccante per la build: serve solo alle operazioni di release, che
    # verificano l'autenticazione nel proprio script.
    detail = "autenticato" if ok else "non autenticato (gh auth login)"
    return Check("gh auth", ok, False, detail)


def check_disk() -> Check:
    usage = shutil.disk_usage(ROOT)
    free_gb = usage.free / (1024 ** 3)
    ok = free_gb >= MIN_FREE_GB
    warning = ok and free_gb < WARN_FREE_GB
    detail = f"{free_gb:.0f} GB liberi (minimo {MIN_FREE_GB} GB)"
    if warning:
        detail += " — consigliati 160 GB"
    return Check("disk", ok, not ok, detail)


def check_visual_studio() -> Check:
    """Chromium 158 richiede Visual Studio 2026 (>=18.0), non VS 2022."""
    vswhere = _program_files_x86() / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere.is_file():
        return Check("visual studio", False, True,
                     "vswhere assente: VS 2026 non installato")
    result = subprocess.run(
        [str(vswhere), "-latest", "-products", "*",
         "-version", "[18.0,19.0)", "-requires",
         "Microsoft.VisualStudio.Component.VC.CoreBuildTools",
         "-property", "installationVersion"],
        capture_output=True, text=True, timeout=30, check=False)
    version = result.stdout.strip().splitlines()
    if not version:
        return Check("visual studio", False, True,
                     "VS 2026 (>=18.0) con Desktop C++ non trovato")

    paths = subprocess.run(
        [str(vswhere), "-latest", "-products", "*",
         "-version", "[18.0,19.0)", "-requires",
         "Microsoft.VisualStudio.Component.VC.CoreBuildTools",
         "-property", "installationPath"],
        capture_output=True, text=True, timeout=30, check=False)
    path = paths.stdout.strip().splitlines()
    if not path:
        return Check("visual studio", False, True,
                     "percorso di VS 2026 non rilevato")
    return Check("visual studio", True, False,
                 f"VS {version[0]} — {path[0]}")


def check_windows_sdk() -> Check:
    """Il pin richiede SDK 10.0.28000; il solo 26100 non basta."""
    sdk = _program_files_x86() / "Windows Kits" / "10" / "Include"
    if not sdk.is_dir():
        return Check("windows sdk", False, True, "Windows SDK non installato")
    versions = sorted((entry.name for entry in sdk.iterdir() if entry.is_dir()),
                      reverse=True)
    if not versions:
        return Check("windows sdk", False, True, "nessuna versione SDK")

    def key(value: str) -> tuple[int, ...]:
        parts: list[int] = []
        for part in value.split("."):
            if not part.isdigit():
                break
            parts.append(int(part))
        return tuple(parts)

    eligible = [value for value in versions if key(value) >= (10, 0, 28000)]
    if not eligible:
        return Check("windows sdk", False, True,
                     f"serve 10.0.28000+, trovato {versions[0]}")
    return Check("windows sdk", True, False,
                 f"{eligible[0]} (richiesto 10.0.28000+)")


def check_depot_tools() -> Check:
    missing = [name for name in ("gclient", "gn", "autoninja")
               if not shutil.which(name)]
    if missing:
        return Check("depot_tools", False, True,
                     "mancano: " + ", ".join(missing))
    return Check("depot_tools", True, False, shutil.which("gclient") or "")


def check_ram() -> Check:
    if platform.system() != "Windows":
        return Check("ram", True, False, "non Windows: controllo saltato")
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"],
            capture_output=True, text=True, timeout=30, check=False)
        total_gb = int(result.stdout.strip()) / (1024 ** 3)
    except (ValueError, OSError, subprocess.SubprocessError):
        return Check("ram", True, False, "non rilevabile")
    ok = total_gb >= 15
    return Check("ram", ok, not ok, f"{total_gb:.0f} GB")


def run_checks(skip_toolchain: bool) -> list[Check]:
    checks = [check_versions(), check_python(), check_tool("git", ["--version"]),
              check_tool("gh", ["--version"]), check_gh_auth()]
    if skip_toolchain:
        return checks
    checks.extend([
        check_disk(),
        check_ram(),
        check_visual_studio(),
        check_windows_sdk(),
        check_depot_tools(),
    ])
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-toolchain", action="store_true",
                        help="salta VS/SDK/depot_tools/disco (CI)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    checks = run_checks(args.skip_toolchain)
    if args.json:
        print(json.dumps([asdict(check) for check in checks], indent=2))
    else:
        print(f"Preflight Umbrella — {platform.platform()}")
        for check in checks:
            state = "OK " if check.ok else ("ERR" if check.blocking else " ! ")
            print(f"[{state}] {check.name:16} {check.detail}")

    blocking = [check for check in checks if check.blocking and not check.ok]
    if blocking:
        print(f"\n{len(blocking)} requisiti bloccanti non soddisfatti.",
              file=sys.stderr)
        print("Vedi docs/BUILD.md per l'installazione della toolchain.",
              file=sys.stderr)
        return 1
    print("\nRequisiti minimi soddisfatti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
