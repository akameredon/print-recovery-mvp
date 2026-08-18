# Build a standalone Print Recovery folder with PyInstaller
# Run this on a Windows machine that has Python 3.11+ installed.
#
# Usage (from repository root):
#   powershell -ExecutionPolicy Bypass -File packaging\windows\build-exe.ps1
#
# Output:
#   dist\PrintRecovery\   <-- copy this whole folder or feed it to the installer

[CmdletBinding()]
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

Write-Host "=== Print Recovery — Build Standalone Executable ===" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python is not on PATH. Install Python 3.11+ from https://www.python.org and tick 'Add to PATH'."
}

$version = & python --version 2>&1
Write-Host "Using: $version"

# Ensure build tools
Write-Host "Installing/upgrading PyInstaller and runtime dependencies..."
& python -m pip install --upgrade pip
& python -m pip install -r requirements.txt
& python -m pip install "pyinstaller>=6.0"

if ($Clean) {
    Write-Host "Cleaning previous build folders..."
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue dist, build
}

$spec = Join-Path $ProjectRoot "packaging\windows\print-recovery.spec"
if (-not (Test-Path $spec)) {
    throw "Spec file not found: $spec"
}

Write-Host "Running PyInstaller..."
& python -m PyInstaller --noconfirm $spec

$outDir = Join-Path $ProjectRoot "dist\PrintRecovery"
if (-not (Test-Path (Join-Path $outDir "PrintRecovery.exe"))) {
    throw "Build finished but PrintRecovery.exe was not found in $outDir"
}

# Create empty data/output folders so the app can write on first run
New-Item -ItemType Directory -Force -Path (Join-Path $outDir "data"), (Join-Path $outDir "outputs") | Out-Null

# Copy a starter config if missing
$exampleConfig = Join-Path $ProjectRoot "config.example.json"
$targetConfig  = Join-Path $outDir "config.json"
if ((Test-Path $exampleConfig) -and -not (Test-Path $targetConfig)) {
    Copy-Item $exampleConfig $targetConfig
}

Write-Host ""
Write-Host "SUCCESS" -ForegroundColor Green
Write-Host "Standalone folder is ready at:"
Write-Host "  $outDir"
Write-Host ""
Write-Host "You can now:"
Write-Host "  1. Double-click PrintRecovery.exe inside that folder to test"
Write-Host "  2. Or run the Inno Setup script to create a real installer"
Write-Host ""
