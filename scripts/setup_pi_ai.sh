#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
sudo apt update
sudo apt install -y python3-venv python3-pip unzip wget chromium
if [[ ! -d .venv ]]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install vosk
.venv/bin/python scripts/install_image_from_repo.py
if [[ ! -d models/speech/vosk-model-small-en-us-0.15 ]]; then
  mkdir -p models/speech
  wget -O /tmp/letterstars-vosk.zip https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
  unzip -q /tmp/letterstars-vosk.zip -d models/speech
fi
echo "Installed model files. Launch with: .venv/bin/python -m web_app.server"
