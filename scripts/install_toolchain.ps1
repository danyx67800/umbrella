# Copyright 2026 The Umbrella Authors
# Installa la toolchain Windows richiesta da Chromium 158:
#   Visual Studio 2026 Build Tools 18.x (Desktop C++ + ATL/MFC)
#   Windows SDK 10.0.28000 (tutte le feature, inclusi Debugging Tools)
#
# Va eseguito con privilegi amministratore:
#   powershell -ExecutionPolicy Bypass -File scripts/install_toolchain.ps1
#
# Non installa depot_tools (nessun privilegio richiesto, vedi docs/BUILD.md).

#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$root = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $root ".cache"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "toolchain-install.log"
$done = Join-Path $logDir "toolchain-install.done"
$failed = Join-Path $logDir "toolchain-install.failed"

Remove-Item $done, $failed -Force -ErrorAction SilentlyContinue

function Write-Log([string]$Message) {
    $line = "[$(Get-Date -Format 'HH:mm:ss')] $Message"
    Write-Host $line
    $line | Out-File -FilePath $log -Encoding utf8 -Append
}

function Finish([int]$Code) {
    if ($Code -eq 0) {
        "ok $(Get-Date -Format o)" | Out-File -FilePath $done -Encoding utf8
    } else {
        "exit=$Code $(Get-Date -Format o)" | Out-File -FilePath $failed -Encoding utf8
    }
    exit $Code
}

Write-Log "== Umbrella toolchain: VS 2026 + Windows SDK 28000 =="

# Chromium usa percorsi molto profondi: abilitare i long paths a livello sistema.
$fs = "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem"
Set-ItemProperty -Path $fs -Name LongPathsEnabled -Value 1 -Type DWord
Write-Log "LongPathsEnabled=1"

$git = (Get-Command git.exe -ErrorAction SilentlyContinue).Source
if ($git) {
    & $git config --system core.longpaths true
    Write-Log "git core.longpaths=true"
}

# depot_tools deve usare il Visual Studio locale, non il toolchain CIPD.
[Environment]::SetEnvironmentVariable("DEPOT_TOOLS_WIN_TOOLCHAIN", "0", "Machine")
Write-Log "DEPOT_TOOLS_WIN_TOOLCHAIN=0 (machine)"

$vsInstall = "C:\Program Files\Microsoft Visual Studio\2026\BuildTools"
$vsInstaller = Join-Path $env:TEMP "vs_BuildTools_2026_umbrella.exe"
if (-not (Test-Path $vsInstaller)) {
    Write-Log "Download VS 2026 Build Tools 18.12.1"
    Invoke-WebRequest -Uri "https://download.visualstudio.microsoft.com/download/pr/646c5a89-4d3a-4f43-985e-9c4c6771f304/6a3058c089e2564cac188178cf918d4cca106ea007f04c9f8bc52d7f5d7fe20f/vs_BuildTools.exe" -OutFile $vsInstaller
}

$vsArgs = @(
    "--quiet", "--wait", "--norestart", "--nocache",
    "--installPath", $vsInstall,
    "--add", "Microsoft.VisualStudio.Workload.NativeDesktop",
    "--add", "Microsoft.VisualStudio.Component.VC.ATLMFC",
    "--includeRecommended"
)

Write-Log "Avvio installer VS 2026 (20-40 minuti)"
$vs = Start-Process -FilePath $vsInstaller -ArgumentList $vsArgs -Wait -PassThru
Write-Log "VS installer exit=$($vs.ExitCode)"
if ($vs.ExitCode -notin @(0, 3010)) {
    Write-Log "Installazione VS fallita"
    Finish $vs.ExitCode
}

if (Test-Path $vsInstall) {
    [Environment]::SetEnvironmentVariable("vs2026_install", $vsInstall, "Machine")
    Write-Log "vs2026_install=$vsInstall (machine)"
}

$sdkInstaller = Join-Path $env:TEMP "winsdksetup_28000_umbrella.exe"
if (-not (Test-Path $sdkInstaller)) {
    Write-Log "Download Windows SDK 10.0.28000.2957"
    Invoke-WebRequest -Uri "https://download.microsoft.com/download/e6cfffdc-0d3e-4c6c-96d7-d491da459a07/KIT_BUNDLE_WINDOWSSDK_MEDIACREATION/winsdksetup.exe" -OutFile $sdkInstaller
}

Write-Log "Avvio installer Windows SDK (tutte le feature)"
$sdk = Start-Process -FilePath $sdkInstaller -ArgumentList @("/features", "+", "/q", "/norestart") -Wait -PassThru
Write-Log "SDK installer exit=$($sdk.ExitCode)"
if ($sdk.ExitCode -notin @(0, 3010)) {
    Write-Log "Installazione SDK fallita"
    Finish $sdk.ExitCode
}

$sdkDir = "C:\Program Files (x86)\Windows Kits\10\Include\10.0.28000.0"
if (-not (Test-Path $sdkDir)) {
    Write-Log "ERRORE: SDK 10.0.28000.0 non trovato in $sdkDir"
    Finish 1
}

Write-Log "Toolchain installata: VS 2026 + SDK 10.0.28000.0"
Finish 0
