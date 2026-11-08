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

For one-file install, OS/project/dependency updates, Vosk download and app launch
on Raspberry Pi OS **64-bit Desktop**, run `bash setup_raspberry.sh`.
The installer can also be copied outside the repository: it clones the project
to `~/lingo-step` if needed. Run it as your normal user, without `sudo`.
Later launches only need `bash scripts/run_pi.sh`.
See [Arabic setup instructions](docs/RASPBERRY_SETUP_AR.md).

```bash
git clone https://github.com/Abdulrhaman0-0/lingo-step.git
cd lingo-step
bash setup_raspberry.sh
```

GitHub repository is public: cloning needs no authentication; pushing still requires write access. `python3 main.py` also works once Python's dependencies are available in the active environment.

**Current image model:** The supplied TensorFlow Lite model includes A–Z plus `others` (27 classes). The binary, labels and matching config are in `models/image/`. A winning `others` prediction is rejected without saving a failed attempt or selecting a runner-up letter. Actual camera accuracy and preprocessing still need validation with real cards/backgrounds. Vosk English model downloads during Pi setup. See [image-model test steps](docs/AE_MODEL_DESKTOP_TEST.md).

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
models/image/                  # Supplied A–Z + others TFLite model and config
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
