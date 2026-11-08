# LingoStep — Deployment and acceptance (Python application + parent website)

**Main product:** Raspberry Pi 5 native Python touch app, launched with `python3 main.py` (or `.venv/bin/python main.py`).

**Cloud product:** Separate, authenticated Flask guardian website, launched on a real HTTPS server; not part of the child's desktop UI.

## Step 0 — what is complete and what is NOT

**Implemented in Python:** child profile selection, data isolation, lesson/navigation, real-device adapters, asynchronous Vosk microphone hook, USB-camera preview, persisted student attempts, and offline-first HTTPS sync. Web portal has parent signup/sign-in, private child pairing and a live achievements dashboard. UI and portal unit tests run on GitHub CI.

**Not certified:** Raspberry Pi microphone/camera/touchscreen runtime, actual spoken letter recognition, TFJS-to-TFLite model conversion/parity tests, No Card class/accuracy, cloud host/domain/TLS/real guardians, and tests over live network. Do not claim device production-ready until real test evidence exists.

## Step 1 — GitHub access on Raspberry Pi

Create an SSH key for the Raspberry only:

```bash
ssh-keygen -t ed25519 -C "lingostep-pi5"
cat ~/.ssh/id_ed25519.pub
```

Add *public key only* in GitHub Settings → SSH Keys for an account authorized to read the private repository. Test:

```bash
ssh -T git@github.com
```

For the current review branch:

```bash
cd ~
git clone -b feature/python-final-ui-cloud git@github.com:Abdulrhaman0-0/lingo-step.git
cd lingo-step
```

If already cloned: `git fetch origin && git switch feature/python-final-ui-cloud && git pull --ff-only`.

## Step 2 — install dependencies on Pi 5 (Debian Trixie aarch64)

```bash
cd ~/lingo-step
bash scripts/setup_pi_native.sh
```

The script installs system Python/OpenCV/Pillow/ALSA/PortAudio/espeak, virtual environment, Vosk, sounddevice, LiteRT and the small Vosk English model.

Check:

```bash
.venv/bin/python -c "import cv2,PIL,vosk,sounddevice; print('Base dependencies OK')"
v4l2-ctl --list-devices
arecord -l
espeak-ng -v en 'The letter A'
```

Use the Raspberry desktop Chromium/VNC only to administer the machine. The child app does **not** need Chromium.

## Step 3 — native image model handoff

Original Teachable Machine `model.json`, `weights.bin`, `metadata.json` is a **TFJS model**. Python's LiteRT adapter expects a **genuinely converted** `models/image/model.tflite` and `models/image/config.json`, after conversion and parity validation against the original model on real A–Z cards.

Example config layout (values MUST be verified for the converted model, not guessed):

```json
{
  "labels": ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"],
  "channel_order": "RGB",
  "input_mean": 127.5,
  "input_std": 127.5
}
```

Never rename `model.json` to `model.tflite`. Without it the camera preview still works and visibly says image inference is unavailable.

The image model currently has no explicit `NO_CARD` class; it can misclassify blank scenes with high confidence. Test on false positives and acquire more training data if required.

## Step 4 — start the child app

```bash
cd ~/lingo-step
.venv/bin/python main.py
```

Create or select an existing child; test Home → Learn (sound and Vosk) → Revision (camera and valid/invalid cards) → Achievements. F11 toggles fullscreen; Escape leaves fullscreen. Rotate display to landscape using Raspberry Pi OS display settings if needed.

Local DB is in `data/progress.db`, excluded from Git.

## Step 5 — launch guardian website on a separate cloud server

Install Python 3.11+ on cloud host with persistent disk. From repository root:

```bash
python3 -m venv .cloud-venv
.cloud-venv/bin/pip install -r cloud/requirements.txt
```

Set **secret environment variables**, e.g. from the hosting provider's secret store:

```bash
export LINGOSTEP_SESSION_SECRET='<generate 32+ random chars, keep secret>'
export LINGOSTEP_DEVICE_TOKEN='<generate 24+ random chars, keep secret>'
export LINGOSTEP_CLOUD_DB='/persistent/portal.db'
```

Example generate secrets locally: `python3 -c "import secrets;print(secrets.token_urlsafe(48))"`. Never commit secret values.

Run behind a **managed TLS reverse proxy** (e.g. Caddy/Nginx, or a platform providing HTTPS):

```bash
.cloud-venv/bin/gunicorn -w 2 -b 127.0.0.1:8080 cloud.wsgi:app
```

Public HTTPS address, domain and hosting service must be supplied/configured externally. Do not expose development Flask server to the internet. Cloud API persists DB on host; add secure backups, rate limiting, abuse protection, log retention and account recovery before any broad public deployment.

For a development-only local test, set `LINGOSTEP_COOKIE_SECURE=0` and run `python -m cloud.portal` on localhost; do not use that setting on a live HTTPS host.

## Step 6 — sync device attempts to Cloud

On Raspberry (with secure HTTPS cloud domain), set matching variables in terminal/session or an environment file with mode 600:

```bash
export LINGOSTEP_CLOUD_URL='https://YOUR_REAL_DOMAIN'
export LINGOSTEP_DEVICE_TOKEN='SAME_PRIVATE_DEVICE_TOKEN_USED_ON_CLOUD'
.venv/bin/python main.py
```

The app writes records to SQLite first and starts asynchronous sync. Reconnects retry pending events. Server ingestion is idempotent by UUID: re-sending an attempt does not count it twice. No raw photos/audio are uploaded.

Guardian creates an account at the cloud website with a strong password; from child app → Achievements → Parent Pairing Code, copy the high-entropy code into the website's pairing form **after first successful sync**. Only that authenticated guardian may view that child's dashboard.

## Step 7 — real acceptance tests (required)

1. UI launch + touchscreen: all five pages; Arabic RTL text legibility, landscape scaling, no stuck mouse/keyboard assumptions.
2. Two distinct students: unique profiles, attempted letters and achievements correctly separated, persistent across restart.
3. Speaker/USB mic: audio output, Vosk download, letter-name recognition, retry/no-recognition case, B/D/T and other confusions. Vosk **does not grade pronunciation quality**.
4. USB webcam: 640×480 capture, valid TFLite model + correct label order, no synthetic confidence, five stable frames; low confidence not recorded as a success.
5. Wrong-card and no-card checks; calculate *empirical* per-letter precision/recall, not merely confidence threshold.
6. Cloud offline/online: record attempts while Wi-Fi off, reconnect, check upload count, repeat upload, confirm no duplicate.
7. Guardian portal: signup/login, pairing code, second parent cannot see the first parent's child, logout, responsive mobile view.
8. Power-cycle Raspberry Pi: saved data remains, no data loss. Cloud recovery, HTTPS, and credentials verified.

Only after these are complete should the feature PR be merged into `main`; then Pi can use `git switch main && git pull --ff-only origin main`.
