[CmdletBinding()]
param(
    [string]$ProjectRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [int]$Port = 5173
)

$ErrorActionPreference = "Stop"
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python 3 is required. Install the approved runtime before starting Print Recovery."
}
$app = Join-Path $ProjectRoot "app.py"
if (-not (Test-Path -LiteralPath $app)) {
    throw "app.py was not found under $ProjectRoot."
}
$dataDir = Join-Path $ProjectRoot "data"
$outputDir = Join-Path $ProjectRoot "outputs"
New-Item -ItemType Directory -Force -Path $dataDir, $outputDir | Out-Null
$env:PRINT_RECOVERY_HOST = "127.0.0.1"
$env:PRINT_RECOVERY_PORT = "$Port"
$env:PRINT_RECOVERY_DATA_DIR = $dataDir
$env:PRINT_RECOVERY_OUTPUT_DIR = $outputDir
Write-Host "Starting Print Recovery on http://127.0.0.1:$Port"
& $python.Source $app
if ($LASTEXITCODE -ne 0) {
    throw "Print Recovery exited with code $LASTEXITCODE. Inspect data\print_recovery.log."
}
