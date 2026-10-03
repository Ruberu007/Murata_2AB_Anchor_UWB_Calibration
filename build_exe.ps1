$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$buildPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $buildPython)) {
    throw 'Create .venv and install requirements.txt and requirements-build.txt first. See README.md.'
}
& $buildPython -m PyInstaller --noconfirm UWB_Calibration.spec
if ($LASTEXITCODE -ne 0) { throw 'Executable build failed.' }
Write-Host 'Built dist\UWB_Calibration.exe. Double-click it to start.'
