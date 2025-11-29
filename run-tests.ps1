# Run tests on Windows PowerShell
# Usage: From repository root run: .\run-tests.ps1
# This script creates a venv (or reuses .venv), installs dependencies and runs tests.

$ErrorActionPreference = 'Stop'

Write-Host "Creating virtual environment (if not present)..."
if (-not (Test-Path -Path .\.venv)) {
    python -m venv .venv
}
Write-Host "Activating venv..."
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
. .\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip and setuptools..."
python -m pip install --upgrade pip setuptools wheel

Write-Host "Installing package in editable mode and extras (rest and qa)..."
python -m pip install -e .[rest,qa]

Write-Host "Installing test requirements (this may take a few minutes)..."
python -m pip install -r requirements-test.txt

Write-Host "Installing pytest & coverage (safety)..."
python -m pip install pytest pytest-django coverage

Write-Host "Running test suite via $($PWD)\runtests.py..."
python runtests.py

Write-Host "Done. Tests finished."