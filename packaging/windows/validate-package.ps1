[CmdletBinding()]
param(
    [string]$ProjectRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

$ErrorActionPreference = "Stop"
$required = @(
    "app.py",
    "config.py",
    "migrations.py",
    "requirements.txt",
    "data",
    "outputs"
)
$missing = @($required | Where-Object { -not (Test-Path -LiteralPath (Join-Path $ProjectRoot $_)) })
if ($missing.Count -gt 0) {
    throw ("Missing package items: " + ($missing -join ", "))
}
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python 3 is not available on PATH."
}
$version = & $python.Source --version 2>&1
Write-Output "Python runtime: $version"
Write-Output "Project root: $ProjectRoot"
Write-Output "Package preflight passed. No service registration or data mutation was performed."
