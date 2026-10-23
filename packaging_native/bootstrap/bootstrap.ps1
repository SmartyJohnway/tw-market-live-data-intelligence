param([string]$Python = 'python', [string]$BundleRoot = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$env:PYTHONPATH = $null
$env:PYTHONHOME = $null
$env:PYTHONDONTWRITEBYTECODE = '1'
& $Python -B "$PSScriptRoot\bootstrap.py" --bundle $BundleRoot
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
