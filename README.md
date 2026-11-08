# LingoStep — Salma STEM Capstone

**Native Python touchscreen application for Raspberry Pi 5**, teaching and reviewing **English letters A–Z**, with an independent **guardian Cloud portal** for reviewing student progress.

> The default `main` branch contains the Python-first implementation. The child's application is started with **`python3 main.py`**, not a browser. The old TensorFlow.js web-only prototype is *not* the product architecture.

## Screens

| Child's Python application | Parent's secure web portal |
|---|---|
| Welcome: create/select child | Guardian registration/login |
| Three-card Home | Pair child via private code |
| Learn: large letter, Listen, Vosk mic | Stars and mastered letters |
| Revision: USB webcam, audio hint, Next/Previous | Achievements and attempts |
| Achievements and private parent pairing code | Mobile-friendly RTL dashboard |

Native UI references: six images supplied in the project conversation on 2026-11-08. Artwork is recreated using Pillow + Tkinter, and scales to Raspberry Pi screen; portrait rotation/legibility needs on-device approval.

## Start on Raspberry Pi

```bash
git clone git@github.com:Abdulrhaman0-0/lingo-step.git
cd lingo-step
bash scripts/setup_pi_native.sh
.venv/bin/python main.py
```

Private GitHub repo requires an authorized SSH key. `python3 main.py` also works once Python's dependencies are available in the active environment.

**AI assets not yet supplied in Python-native format:** Vosk language model downloads during Pi setup, while camera's actual trained Teachable Machine TFJS model must be converted and validated as `models/image/model.tflite` + `config.json`. Without it, camera preview still works but inference is disabled explicitly.

## Parent cloud site

```bash
python3 -m venv .cloud-venv
.cloud-venv/bin/pip install -r cloud/requirements.txt
# Set strong LINGOSTEP_SESSION_SECRET and LINGOSTEP_DEVICE_TOKEN
.cloud-venv/bin/gunicorn -w 2 -b 127.0.0.1:8080 cloud.wsgi:app
```

Reverse proxy HTTPS/domain/credentials/hosting not included. Device sync settings: `LINGOSTEP_CLOUD_URL` (HTTPS) and `LINGOSTEP_DEVICE_TOKEN`. Records queue locally in SQLite if cloud is offline; authenticated guardian pairing is required to see progress.

## Structure

```text
main.py                        # Native Python app entrypoint
letterstars/ui/final_ui.py      # Child Pillow/Tkinter touch UI
letterstars/services/lesson.py # Real lesson evaluation (no mock)
letterstars/adapters/          # OpenCV camera, LiteRT image AI, Vosk speech, audio
letterstars/infrastructure/    # Per-child SQLite + background cloud outbox
cloud/portal.py                # Parent Flask authentication, dashboard & API
cloud/templates/               # Responsive parent website
models/image/                  # Converted, validated TFLite model (pending)
models/speech/                 # Vosk acoustic model (downloaded at setup)
tests/                         # Python 3.11 and 3.13 CI tests
docs/FINAL_DELIVERY_CHECKLIST.md
docs/FINAL_DEPLOYMENT.md
```

## Quality and privacy

- Profiles get stable random IDs; no child's record is accidentally assigned by name.
- Evaluation saves only actual model predictions after confidence filtering. **Vosk letter-name recognition does not assess child's pronunciation quality.**
- No raw child photos/audio transmitted to cloud, only attempts. Private portal requires guardian login + per-child pairing code.
- Cloud deployment needs HTTPS, persistent backups and operational security review.
- Test on *actual* Raspberry Pi 5, touchscreen, USB camera, USB microphone, speaker, plus network, before final signoff.
- Unit tests (not hardware tests): `python -m unittest discover -s tests -v`

See **[Final delivery checklist](docs/FINAL_DELIVERY_CHECKLIST.md)** and **[Deployment runbook](docs/FINAL_DEPLOYMENT.md)** for precise remaining tasks. This `main` source has passed automated tests but remains a **device/cloud acceptance candidate**, not hardware-certified. Physical hardware and hosted cloud validation remain separate acceptance gates.
