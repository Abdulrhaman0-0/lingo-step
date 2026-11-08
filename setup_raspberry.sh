#!/usr/bin/env bash
# Run as your normal desktop user: bash setup_raspberry.sh
set -Eeuo pipefail
trap 'printf "\nSetup failed at line %s. Fix the error above and run this file again.\n" "$LINENO" >&2' ERR

main() {
    local run_app=1 system_update=1 git_update=1
    local arg script_dir project_dir branch model_dir archive download_dir
    for arg in "$@"; do
        case "$arg" in
            --no-run) run_app=0 ;;
            --skip-system-update) system_update=0 ;;
            --skip-git-update) git_update=0 ;;
            --help)
                printf '%s\n' 'Usage: bash setup_raspberry.sh [--no-run] [--skip-system-update] [--skip-git-update]'
                return ;;
            *) printf 'Unknown option: %s\n' "$arg" >&2; return 1 ;;
        esac
    done
    if [[ "$(uname -s)" != Linux || "$(uname -m)" != aarch64 ]]; then
        echo 'Use Raspberry Pi OS 64-bit Desktop (aarch64), not Windows or 32-bit OS.' >&2
        return 1
    fi
    if [[ "$EUID" -eq 0 ]]; then
        echo 'Run without sudo: bash setup_raspberry.sh (sudo is used only for system packages).' >&2
        return 1
    fi
    script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
    if [[ -f "$script_dir/main.py" ]]; then
        project_dir="$script_dir"
    else
        project_dir="$HOME/lingo-step"
    fi

    echo '[1/6] Updating Raspberry Pi OS and installing system dependencies...'
    sudo -v
    sudo apt-get update
    if [[ "$system_update" -eq 1 ]]; then
        sudo apt-get full-upgrade -y
    fi
    sudo apt-get install -y git ca-certificates curl unzip \
        python3 python3-pip python3-venv python3-tk python3-opencv \
        python3-pil python3-pil.imagetk python3-numpy \
        fonts-noto-core fonts-dejavu-core libraqm0 \
        espeak-ng v4l-utils alsa-utils pipewire-bin pulseaudio-utils portaudio19-dev libportaudio2 \
        libatomic1 libgomp1

    echo '[2/6] Downloading/updating LingoStep...'
    if [[ ! -d "$project_dir" ]]; then
        git clone --branch main --single-branch https://github.com/Abdulrhaman0-0/lingo-step.git "$project_dir"
    elif [[ ! -d "$project_dir/.git" ]]; then
        echo "Not a Git checkout: $project_dir. Move this installer outside that folder and retry." >&2
        return 1
    elif [[ "$git_update" -eq 1 ]]; then
        if [[ -n "$(git -C "$project_dir" status --porcelain)" ]]; then
            echo 'Local changes found. Save/commit them, or use --skip-git-update to install this local copy.' >&2
            return 1
        fi
        branch="$(git -C "$project_dir" branch --show-current)"
        if [[ "$branch" != main ]]; then
            echo 'Switch to main first, or use --skip-git-update to keep your current branch.' >&2
            return 1
        fi
        git -C "$project_dir" pull --ff-only origin main
    fi
    cd -- "$project_dir"

    echo '[3/6] Installing/updating Python dependencies...'
    if [[ -e .venv && ! -x .venv/bin/python ]]; then
        echo 'This .venv belongs to another OS or is incomplete. Rename it and run setup again.' >&2
        return 1
    fi
    python3 -m venv --system-site-packages .venv
    .venv/bin/python -m pip install --upgrade pip setuptools wheel
    .venv/bin/python -m pip install --upgrade -r requirements-pi.txt -r requirements-ui.txt

    echo '[4/6] Installing offline Vosk English model...'
    model_dir='models/speech/vosk-model-small-en-us-0.15'
    if [[ ! -s "$model_dir/am/final.mdl" || ! -s "$model_dir/conf/model.conf" || ! -s "$model_dir/graph/Gr.fst" ]]; then
        mkdir -p models/speech
        download_dir="$(mktemp -d "$project_dir/.venv/vosk-download-XXXXXX")"
        archive="$download_dir/vosk.zip"
        curl --fail --location --retry 3 --connect-timeout 30 \
            --output "$archive" https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
        unzip -tq "$archive"
        unzip -qo "$archive" -d models/speech
        rm -- "$archive"
        rmdir -- "$download_dir"
    fi

    echo '[5/6] Checking UI, camera libraries, speech and image model...'
    .venv/bin/python - <<'PY'
import os
import tkinter
import cv2
import numpy
import PIL.ImageTk
import arabic_reshaper
import bidi
import sounddevice as sd
from ai_edge_litert.interpreter import Interpreter
from letterstars.adapters.vosk_speech import VoskSpeechClassifier, microphone_rate
from letterstars.adapters.image_model import TFLiteImageClassifier
from letterstars.ui.final_ui import ScreenPainter

speech = VoskSpeechClassifier(os.environ.get(
    "LINGOSTEP_VOSK_MODEL", "models/speech/vosk-model-small-en-us-0.15"))
if not speech.ready:
    raise SystemExit("Vosk failed: " + speech.error)
image = TFLiteImageClassifier("models/image")
if not image.ready:
    raise SystemExit("Image model failed: " + image.error +
                     "\nProvide models/image/model.tflite and its matching config.json, then retry.")
ScreenPainter().render("welcome")
print("UI, OpenCV, Vosk and image model OK. Image classes:", ", ".join(image.labels))
try:
    device = sd.query_devices(speech.device, "input")
    rate = microphone_rate(speech.device, speech.rate)
    print("Microphone:", device["name"], "sample rate:", rate)
except (sd.PortAudioError, ValueError) as exc:
    print("MICROPHONE CHECK:", exc, "\nConnect/select a microphone before using speech.")
PY
    v4l2-ctl --list-devices || echo 'Connect a USB webcam before using Revision.'
    if [[ -f /var/run/reboot-required ]]; then
        echo 'System updates require a reboot. After reboot, use: .venv/bin/python main.py'
    fi
    echo "[6/6] Setup complete. Project: $project_dir"
    echo 'Next time from the project folder: .venv/bin/python main.py'
    if [[ "$run_app" -eq 1 ]]; then
        if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
            echo 'Open a terminal on the Raspberry desktop and run: .venv/bin/python main.py'
            return
        fi
        exec .venv/bin/python main.py
    fi
}

# Keep setup in a function so updating this file through Git does not interrupt it.
main "$@"
