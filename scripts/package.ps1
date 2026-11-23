# Copyright 2026 The Umbrella Authors
# Crea un pacchetto portable da una build Release gia' completata.
# Non e' un installer: l'installer firmato e' previsto in Fase 7.

param(
    [string]$OutDir = "out/Umbrella",
    [string]$Version = "",
    [switch]$SkipArchive
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$src = Join-Path $root "chromium/src"
$out = Join-Path $src $OutDir
$exe = Join-Path $out "chrome.exe"

if (-not (Test-Path $exe)) {
    throw "Build non trovata: $exe. Esegui prima scripts/build.py --release."
}

if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = (Get-Content (Join-Path $root "VERSION") -Raw).Trim()
}

$distRoot = Join-Path $root "dist"
$stage = Join-Path $distRoot "Umbrella-$Version-win64"
if (Test-Path $stage) {
    Remove-Item $stage -Recurse -Force
}
New-Item -ItemType Directory -Path $stage -Force | Out-Null

$skipExtensions = @(".pdb", ".lib", ".exp", ".ilk", ".obj")
$skipNames = @("args.gn", "build.ninja", ".ninja_log", ".ninja_deps")

Get-ChildItem -Path $out -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($out.Length + 1)
    if ($relative -match "^(obj|gen)\\]") { return }
    if ($skipExtensions -contains $_.Extension.ToLowerInvariant()) { return }
    if ($skipNames -contains $_.Name) { return }
    if ($_.Name -like ".ninja*") { return }

    $destination = Join-Path $stage $relative
    $destinationDir = Split-Path -Parent $destination
    if (-not (Test-Path $destinationDir)) {
        New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
    }
    Copy-Item $_.FullName $destination
}

$manifest = @(
    "Umbrella $Version",
    "Chromium $(Get-Content (Join-Path $root 'versions.json') -Raw | ConvertFrom-Json | Select-Object -ExpandProperty chromium | Select-Object -ExpandProperty tag)",
    "Built $(Get-Date -Format o)"
)
$manifest | Set-Content (Join-Path $stage "UMBRELLA-BUILD.txt") -Encoding UTF8

$hashLines = Get-ChildItem -Path $stage -Recurse -File |
    Where-Object { $_.Name -ne "SHA256SUMS" } |
    ForEach-Object {
        $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        $relative = $_.FullName.Substring($stage.Length + 1)
        "$hash  $relative"
    }
$hashLines | Set-Content (Join-Path $stage "SHA256SUMS") -Encoding ASCII

Write-Host "Pacchetto preparato: $stage"
Write-Host "File: $((Get-ChildItem $stage -Recurse -File).Count)"

if (-not $SkipArchive) {
    $zip = Join-Path $distRoot "Umbrella-$Version-win64.zip"
    if (Test-Path $zip) { Remove-Item $zip -Force }
    Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zip
    Write-Host "Archivio: $zip"
}
