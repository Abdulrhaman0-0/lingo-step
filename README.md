# LingoStep — Salma STEM Capstone

Offline-first **Python / Tkinter + Pillow** touchscreen educational app for **English letters A–Z**, built for Raspberry Pi 5 and Touch Display 2.

## UI v2 (November 7, 2026)
The screens were redesigned from the team's four reference images:
1. Arabic welcome screen with child-name field.
2. Three large rounded cards: learning / revision / progress.
3. Alphabet learning card with huge letter and Listen / Speak / Previous / Next.
4. Revision with camera area and listen control.
5. Progress with stars, counters and recent attempts.

The colorful LingoStep wordmark is drawn locally, with no internet image dependency.

**Important:** The child's name currently identifies an in-memory session; SQLite attempts are not yet separated by child profile. Do not present this as full multi-account persistence.

### Laptop setup
Install Python 3.10+ with Tkinter. Run from the repository root:

```bash
python -m pip install -r requirements-ui.txt
python main.py
```

On Windows, `py main.py` may be used. F11 toggles fullscreen; Esc exits fullscreen.

### Raspberry Pi 5
Touch Display 2 is physically 720 × 1280 portrait; **rotate it to landscape** in Raspberry Pi OS Desktop (Control Centre / Screens) for this UI. It scales to fill 1280 × 720 when rotated. In portrait, the landscape layout is letterboxed and controls may be too small for children.

```bash
sudo apt update
sudo apt install python3-tk python3-pil fonts-noto-core espeak-ng python3-opencv python3-numpy
python3 main.py
```

These are installation starting points, **not evidence of deployment or touch hardware testing**. Camera and sound hardware need separate acceptance tests. Optional laptop camera: `pip install -r requirements-camera.txt`.

### Repository structure
```text
main.py                           Dependency injection / composition
letterstars/ui/desktop.py         Stable import point
letterstars/ui/lingo_ui.py        Illustrated Tkinter UI (no AI algorithms)
letterstars/domain/               Pure business rules and data classes
letterstars/services/             Learn and revision use cases / ports
letterstars/adapters/             Voice, webcam, TFLite image, speech placeholder
letterstars/infrastructure/       Local SQLite attempts
models/image/                     Awaiting real exported model + labels
models/speech/                    Awaiting speech model
docs/                             Capstone metrics, AI handoff, Arabic lesson notes
tests/                            Headless unit and UI render tests
```

### Tests
```bash
python -m unittest discover -s tests -v
```

### AI integration honesty and safety
- Image and speech model files **are not shipped**; no fabricated predictions.
- Real image inference requires a compatible TFLite model under `models/image/`.
- A 5-letter model cannot recognize the other 21 letters even though the UI navigates A–Z.
- Confidence threshold 0.80 is **not** measured accuracy; capstone evaluation separately requires >=80% proven AI accuracy.
- Speech letter-name identification is not pronunciation-quality grading.
- Cloud synchronization is planned, not implemented; the finished STEM exhibit must satisfy IoT/cloud requirements separately.
- Do not publish identifiable children's photos, voice recordings, or private datasets.
