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

For the hosted school prototype, see [PythonAnywhere setup](docs/PYTHONANYWHERE_SETUP_AR.md).
The Raspberry can save its remote connection once using `scripts/configure_cloud.py`
and then launch normally with `scripts/run_pi.sh`.

For the school prototype, hosting is optional. Run the child app and the
simple parent website together on the Raspberry desktop:

```bash
.venv/bin/python scripts/run_demo.py
```

Open `http://127.0.0.1:8080` in a browser **on the same Raspberry** (including
through VNC). Local keys are created once in ignored `data/demo-settings.json`;
the demo portal database is `data/demo-portal.db`. Create a guardian account,
complete a real child attempt, then pair using the code in Achievements.
See [AI handoff and prototype guide](AI_HANDOFF.md) for the full current state.

The following setup is only for a separately hosted website:

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


## Capstone and Raspberry Pi setup materials

The supplied Capstone source materials and the extracted Smart Alphabet Learning starter files are organized under [docs/capstone](docs/capstone/README.md). This includes the searchable official requirements text, supporting research notes, the three-day execution playbook, starter Python files, and testing CSV templates.

For device setup, use the [safe Raspberry Pi setup template](docs/setup/raspberry_pi_setup.example.txt). **Actual Wi-Fi passwords, Pi login passwords, SSH keys, and cloud/API tokens are intentionally not stored in this public repository.** Keep local values in `raspberry_pi_setup.local.txt` (ignored by Git) or enter them directly in Raspberry Pi Imager.

## Autostart on Raspberry Pi 5

To launch LingoStep automatically after the Raspberry Pi desktop signs in:

```bash
cd ~/lingo-step
git pull --ff-only origin main
bash scripts/install_autostart.sh --enable
bash scripts/install_autostart.sh --status
```

Enable **Desktop Autologin** with `sudo raspi-config` if the exhibition device must start without typing a password. Reboot and test with `sudo reboot`. Log: `data/logs/autostart.log`. Disable with `bash scripts/install_autostart.sh --disable`. Full Arabic guide: [Autostart setup](docs/AUTOSTART_RASPBERRY_AR.md).

**Image AI handoff:** `main.py` currently loads `models/image/model.tflite` plus `models/image/config.json`, configured for A–Z + `others` (27 classes). Do **not** replace those files with an unverified ZIP just based on its filename. Check the exported model architecture, labels, input and normalization first. The separately supplied ZIP `4_6019569374568915343.zip` is not yet in this repository or available as a binary attachment in the current request.
