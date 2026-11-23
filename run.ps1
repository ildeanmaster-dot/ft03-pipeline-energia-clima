# Execução ponta a ponta no Windows (PowerShell): cria o ambiente, instala e roda o pipeline.
# Uso: .\run.ps1 [--inicio AAAA-MM-DD] [--fim AAAA-MM-DD] [--areas PA,SP] [--skip-extract]
# Se o PowerShell bloquear scripts: powershell -ExecutionPolicy Bypass -File .\run.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$env:PYTHONPATH = Join-Path $PSScriptRoot "src"

# O PowerShell lê "PA,SP" como lista e repassaria "PA" "SP" separados: junta de novo com vírgula.
$pipelineArgs = @(foreach ($a in $args) { if ($a -is [array]) { $a -join "," } else { $a } })

# Daqui em diante só há chamadas ao Python, conferidas pelo código de saída. Com "Stop", o
# PowerShell 5.1 encerra o script na primeira linha de log (stderr) quando a saída é redirecionada (2>&1).
$ErrorActionPreference = "Continue"

if (-not (Test-Path $py)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
& $py -m pip install --quiet --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py -m pipeline.main @pipelineArgs
exit $LASTEXITCODE
