# LetterStars — Salma STEM Capstone

**Offline-first touchscreen Python desktop app for recognizing English letter cards (A–Z).**

> Status: **working architecture + touch UI + local database + camera adapter + genuine TFLite adapter**.
> **Image and speech models are NOT shipped**; actual camera/AI integration has **not been hardware-tested**.

## التشغيل على اللابتوب (يوم 1)

1. Install **Python 3.10+**, including Tkinter (standard on Windows; some Linux distros require `python3-tk`).
2. Unzip and open the `Salma-LetterStars` folder with VS Code.
3. Open Terminal and run:

```bash
python main.py
```

On Windows, `py main.py` also works. The UI starts fullscreen; press **F11** to toggle and **Esc** to exit fullscreen.

- UI, A–Z selection and SQLite work without third-party packages.
- For an actual USB camera test: `pip install -r requirements-camera.txt` then `python scripts/check_camera.py`.
- For letter speech on Linux: `sudo apt install espeak-ng`. On Windows, built-in PowerShell speech is used.
- Revision AI deliberately remains unavailable until the trained TFLite model is installed.

## Raspberry Pi 5 + Touch Display 2

The 7-inch display is **720×1280 native portrait**. Raspberry Pi OS Desktop can rotate it to
landscape in **Preferences → Control Centre → Screens**. Use touch buttons without keyboard.

```bash
sudo apt update
sudo apt install python3-tk espeak-ng python3-opencv python3-pil python3-numpy
python3 main.py
```

These commands are a **deployment starting point**, not a claim of Pi-tested compatibility.
Actual OS packages, Python version, touchscreen rotation, mic/camera permissions and USB
speaker must be verified on the target Pi. No paid API required.

## Responsibility / architecture

```text
main.py                          Composition root (dependency injection)
letterstars/ui/desktop.py        Tkinter touch screens (NO AI algorithm)
letterstars/services/lesson.py   Use cases and application state (NO Tkinter)
letterstars/services/ports.py    Hardware/AI/storage interfaces (contracts)
letterstars/domain/             Entities and pure decision rules
letterstars/adapters/           Camera, letter voice, image model, speech placeholder
letterstars/infrastructure/     SQLite persistence
models/image/                   Real TFLite model + explicit labels/config, when delivered
models/speech/                  Speech AI contract documentation, waiting for model
scripts/                        Laptop/Raspberry Pi smoke tests
 tests/                          Unit tests without hardware
 docs/                           Arabic teaching plan + integration and metrics
```

## Unit tests

```bash
python -m unittest discover -s tests -v
```

## Critical model limitations

- The **UI always supports all A–Z**. A model trained on 5 letters only recognizes those five;
  we never imply 26-class accuracy from a 5-class model.
- No mock prediction is recorded as an actual attempt. The domain rejects source=`mock`.
- `CONFIDENCE_THRESHOLD=0.80` is a runtime filter, **not measured model accuracy**.
- Stable output requires 5 consecutive high-confidence frames; tune empirically.
- Speech recognition and pronunciation scoring are different problems.
- Cloud sync is a **future interface**; local-only operation does not fulfill the cloud/IoT
  requirement of the STEM brief. See `docs/capstone-metrics.md`.
- Sound failure is shown explicitly. Camera/model failure does not fabricate success.

## GitHub publishing

```bash
git init
git add .
git commit -m "Initial LetterStars modular touchscreen app"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/Salma-LetterStars.git
git push -u origin main
```

Create the repository in your GitHub account first and replace YOUR_ACCOUNT.
Do not publish recordings, identifiable photos of children, consent forms, or private datasets.
