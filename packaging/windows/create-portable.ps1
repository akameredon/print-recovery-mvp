# Create a portable folder that can be copied to a flash drive.
# Works in two modes:
#   A) After build-exe.ps1  → copies the standalone dist\PrintRecovery
#   B) Without build       → copies source + creates a simple launcher
#
# Usage (from repository root):
#   powershell -ExecutionPolicy Bypass -File packaging\windows\create-portable.ps1

[CmdletBinding()]
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$OutputFolder = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path "dist\PrintRecovery-Portable")
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

Write-Host "=== Creating Portable Package ===" -ForegroundColor Cyan

$standalone = Join-Path $ProjectRoot "dist\PrintRecovery"
$hasStandalone = Test-Path (Join-Path $standalone "PrintRecovery.exe")

if (Test-Path $OutputFolder) {
    Remove-Item -Recurse -Force $OutputFolder
}
New-Item -ItemType Directory -Force -Path $OutputFolder | Out-Null

if ($hasStandalone) {
    Write-Host "Using already-built standalone executable..."
    Copy-Item -Path "$standalone\*" -Destination $OutputFolder -Recurse -Force
} else {
    Write-Host "No standalone build found — creating source-based portable folder..."
    Write-Host "(You can later run build-exe.ps1 to get a true .exe version)"

    $exclude = @(".git", ".venv", "venv", "__pycache__", "data", "outputs", "dist", "build", "*.pyc", "*.log")
    Get-ChildItem -Force | Where-Object {
        $name = $_.Name
        -not ($exclude | Where-Object { $name -like $_ })
    } | ForEach-Object {
        Copy-Item $_.FullName -Destination $OutputFolder -Recurse -Force
    }

    # Ensure data folders exist
    New-Item -ItemType Directory -Force -Path (Join-Path $OutputFolder "data"), (Join-Path $OutputFolder "outputs") | Out-Null

    # Copy the simple launcher into the portable root
    $bat = Join-Path $PSScriptRoot "Run-PrintRecovery.bat"
    if (Test-Path $bat) {
        Copy-Item $bat (Join-Path $OutputFolder "Run-PrintRecovery.bat") -Force
    }
}

# Always put a clear README inside the portable folder
$readme = @"
Print Recovery — Portable Package
=================================

HOW TO RUN
----------
1. Double-click  Run-PrintRecovery.bat   (or PrintRecovery.exe if present)
2. Open your browser to:  http://127.0.0.1:5173

IMPORTANT
---------
- This is software-only assisted recovery.
- It does NOT control the printer or RIP.
- It does NOT measure physical media position.
- Use it to capture jobs, checkpoints and generate continuation images for operator review.

DATA
----
All job data and logs stay inside the "data" and "outputs" folders next to the program.
You can copy the whole folder to another computer or flash drive.

STOPPING
--------
Close the console window (or the tray icon if you added one later).
"@

Set-Content -Path (Join-Path $OutputFolder "README-PORTABLE.txt") -Value $readme -Encoding UTF8

Write-Host ""
Write-Host "Portable package ready:" -ForegroundColor Green
Write-Host "  $OutputFolder"
Write-Host ""
Write-Host "Copy the whole folder to a flash drive or desktop."
Write-Host ""
