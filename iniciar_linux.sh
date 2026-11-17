#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then echo 'Python 3 não encontrado.'; exit 1; fi
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if [ ! -f .env ]; then cp .env.example .env; echo 'Edite o arquivo .env antes de iniciar.'; exit 0; fi
set -a; source .env; set +a
exec uvicorn main:app --host 127.0.0.1 --port 8000
