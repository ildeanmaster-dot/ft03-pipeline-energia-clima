#!/usr/bin/env bash
# Execução ponta a ponta: cria o ambiente, instala as dependências e roda o pipeline.
# Uso: ./run.sh [--inicio AAAA-MM-DD] [--fim AAAA-MM-DD] [--areas PA,SP] [--skip-extract]
set -euo pipefail
cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || command -v python)}"
if [ ! -d .venv ]; then
  "$PYTHON_BIN" -m venv .venv
fi
if [ -x .venv/bin/python ]; then
  VENV_PY=.venv/bin/python          # Linux / macOS
else
  VENV_PY=.venv/Scripts/python.exe  # Windows (Git Bash)
fi

"$VENV_PY" -m pip install --quiet --disable-pip-version-check -r requirements.txt
PYTHONPATH=src "$VENV_PY" -m pipeline.main "$@"
