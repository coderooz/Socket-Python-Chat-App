#Requires -Version 5.1
# dev.ps1 — helper for local development (Windows PowerShell)
param(
  [ValidateSet("install", "lint", "format", "test", "server", "web", "all")]
  [string]$Task = "all"
)

$ErrorActionPreference = "Stop"
$Py = ".\venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

function Invoke-Step($label, $cmd) {
  Write-Host "`n== $label ==" -ForegroundColor Cyan
  Invoke-Expression $cmd
  if ($LASTEXITCODE -ne 0) { throw "$label failed with exit $LASTEXITCODE" }
}

switch ($Task) {
  "install" { Invoke-Step "pip install" "$Py -m pip install -r requirements-dev.txt" }
  "lint"    { Invoke-Step "ruff check" "$Py -m ruff check ." }
  "format"  { Invoke-Step "ruff format --check" "$Py -m ruff format --check ." }
  "test"    { Invoke-Step "pytest" "$Py -m pytest -v" }
  "server"  { & $Py server.py }
  "web"     { & $Py -m http.server 8000 --directory web }
  "all" {
    Invoke-Step "ruff check" "$Py -m ruff check ."
    Invoke-Step "ruff format --check" "$Py -m ruff format --check ."
    Invoke-Step "pytest" "$Py -m pytest -v"
    Write-Host "`nAll checks passed." -ForegroundColor Green
  }
}
