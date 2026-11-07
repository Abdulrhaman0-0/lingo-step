#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv python3-tk \
 python3-opencv python3-pil python3-numpy espeak-ng v4l-utils \
 alsa-utils portaudio19-dev libportaudio2 unzip wget
if [ ! -d .venv ]; then
  python3 -m venv --system-site-packages .venv
fi
.venv/bin/python -m pip install -r requirements-pi.txt
if [ ! -d models/speech/vosk-model-small-en-us-0.15 ]; then
  mkdir -p models/speech
  wget -O /tmp/lingostep-vosk-en.zip https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
  unzip -q -o /tmp/lingostep-vosk-en.zip -d models/speech
fi
if [ ! -f models/image/model.tflite ] || [ ! -f models/image/config.json ]; then
  echo "NOTICE: Image AI model.tflite + config.json are not yet installed."
  echo "Camera preview still works. Train/convert and validate model before image inference."
fi
echo "Check: .venv/bin/python -c 'import cv2, PIL, vosk, sounddevice; print(\"Modules OK\")'"
echo "Run native Python app: .venv/bin/python main.py"
