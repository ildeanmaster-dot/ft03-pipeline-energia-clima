# Execução ponta a ponta no Windows (PowerShell): cria o ambiente, instala e roda o pipeline.
# Uso: .\run.ps1 [--inicio AAAA-MM-DD] [--fim AAAA-MM-DD] [--areas PA,SP] [--skip-extract]
# Se o PowerShell bloquear scripts: powershell -ExecutionPolicy Bypass -File .\run.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
& $py -m pip install --quiet --disable-pip-version-check -r requirements.txt
$env:PYTHONPATH = Join-Path $PSScriptRoot "src"
& $py -m pipeline.main @args
exit $LASTEXITCODE
