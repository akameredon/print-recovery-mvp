[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$ProjectRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$InstallRoot = "$env:ProgramFiles\PrintRecovery",
    [string]$DataRoot = "$env:ProgramData\PrintRecovery",
    [switch]$SkipDependencies,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$source = (Resolve-Path -LiteralPath $ProjectRoot).Path
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python 3 is required. Install the approved runtime before installing Print Recovery."
}

if ($Uninstall) {
    if (Test-Path -LiteralPath $InstallRoot) {
        Remove-Item -LiteralPath $InstallRoot -Recurse -Force
    }
    Write-Output "Application files removed from $InstallRoot. Data and encrypted keys under $DataRoot were preserved."
    exit 0
}

$required = @("app.py", "config.py", "migrations.py", "requirements.txt")
foreach ($item in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $source $item))) {
        throw "Required source file is missing: $item"
    }
}
New-Item -ItemType Directory -Force -Path $InstallRoot, $DataRoot, (Join-Path $DataRoot "outputs") | Out-Null
$venv = Join-Path $InstallRoot "venv"
if (-not (Test-Path -LiteralPath (Join-Path $venv "Scripts\python.exe"))) {
    & $python.Source -m venv $venv
}
$targetPython = Join-Path $venv "Scripts\python.exe"
if (-not $SkipDependencies) {
    & $targetPython -m pip install --disable-pip-version-check -r (Join-Path $source "requirements.txt")
}
$exclude = @("data", "outputs", ".git", "__pycache__", "*.log", ".local-secrets.key")
Get-ChildItem -LiteralPath $source -Force | Where-Object { $exclude -notcontains $_.Name } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $InstallRoot -Recurse -Force
}
$launcher = Join-Path $InstallRoot "run-print-recovery.ps1"
@"
`$ErrorActionPreference = 'Stop'
`$env:PRINT_RECOVERY_HOST = '127.0.0.1'
`$env:PRINT_RECOVERY_DATA_DIR = '$DataRoot'
`$env:PRINT_RECOVERY_OUTPUT_DIR = '$(Join-Path $DataRoot "outputs")'
& '$targetPython' '$(Join-Path $InstallRoot "app.py")'
"@ | Set-Content -LiteralPath $launcher -Encoding UTF8
$inventory = Get-ChildItem -LiteralPath $InstallRoot -File -Recurse | Where-Object { $_.FullName -notlike "*$([IO.Path]::DirectorySeparatorChar)data$([IO.Path]::DirectorySeparatorChar)*" } | ForEach-Object {
    $hash = Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
    [ordered]@{ path = $_.FullName.Substring($InstallRoot.Length).TrimStart('\'); sha256 = $hash.Hash; bytes = $_.Length }
}
$inventory | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $InstallRoot "install-manifest.json") -Encoding UTF8
Write-Output "Installed Print Recovery to $InstallRoot. Data and encrypted keys remain under $DataRoot."
Write-Output "Launch with: powershell -ExecutionPolicy Bypass -File `"$launcher`""
