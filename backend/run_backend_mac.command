#!/bin/zsh
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3.11 -m venv .venv || python3 -m venv .venv
fi
source .venv/bin/activate
python -m ensurepip --upgrade
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
