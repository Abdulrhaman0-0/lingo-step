# LetterStars: Teachable Machine (A–Z) + Vosk integration

This is a **real model inference path** alongside the original Tkinter application.
The supplied Teachable Machine export uses **TensorFlow.js** (`model.json`, `weights.bin`, `metadata.json`) with 26 labels A–Z, 96×96 grayscale training images.
It is **not** a TFLite model, so the original `TFLiteImageClassifier` cannot load it without conversion.

The new touch UI is served locally on Raspberry Pi OS and runs the **original TFJS model in Chromium**. Vosk transcription runs locally in a Python HTTP server. Both stay on the Pi.

## 1. Install on Raspberry Pi 5 (Debian Trixie / 64-bit)

From repository root:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip unzip wget chromium
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install vosk
```

If `pip install vosk` fails, do not claim the speech part is working. Check the correct aarch64/Python wheel or use an OS-supported environment.

## 2. Install the actual image model

Copy the uploaded `Embedded Image.zip` to the Pi in the repository root, then:

```bash
mkdir -p models/image
unzip -o -j 'Embedded Image.zip' model.json metadata.json weights.bin -d models/image
```

Expected: `models/image/model.json`, `models/image/metadata.json`, and `models/image/weights.bin`.

**These binary weights are not in this GitHub branch.** They are supplied by the team's separate ZIP. The UI refuses to claim image AI is ready when they are missing.

## 3. Install Vosk language model

```bash
mkdir -p models/speech
wget -O /tmp/vosk-en.zip https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip -q /tmp/vosk-en.zip -d models/speech
```

Expected directory: `models/speech/vosk-model-small-en-us-0.15`.

## 4. Start the application

```bash
source .venv/bin/activate
python3 -m web_app.server
```

Open Chromium **on Raspberry Pi itself**, not a remote browser, at:

`http://127.0.0.1:8765`

This preserves browser camera/microphone permission support over localhost. On the touchscreen or by VNC, allow camera and mic access when Chromium asks.

## Acceptance test

1. At startup see `Camera AI ready — 26 letters loaded`.
2. In Learn, press `Listen` and hear the selected letter name.
3. Press `Say the letter`, speak clearly for 2 seconds, and see the **actual Vosk transcript**, not a fabricated success.
4. In Revision, press `New letter`, hear the challenge, press `Start camera`, show the correct printed card, verify the letter prediction (5 stable frames above 0.80).
5. Show an incorrect card and check `Try again`; results appear under Progress and are saved in this browser's localStorage.
6. Test varied lighting, letter font, speakers and letter confusions independently, and record accuracy. **0.80 confidence is not 80% measured accuracy.**

## Important limitations

- The **Image Model is 26-way without a No Card class**. A model can produce a high-confidence wrong prediction on a blank scene. Add no-card training and measured tests before using the system for unattended feedback.
- **Vosk recognizes letter names**, not articulation accuracy. B/D/E and other similar sounds are especially hard to distinguish, and spoken variants may not transcribe as expected. Speech results are provisional.
- No audio samples are uploaded; only Vosk transcript and browser-local progress are retained. No cloud/IoT reporting yet: this remains an outstanding Capstone requirement.
- TensorFlow.js and Teachable Machine JS dependencies are fetched from jsDelivr CDN on first load; **browser app is not fully offline** without vendoring those files.
- Raspberry Pi 5 hardware, USB webcam, touch display, Bluetooth output, Vosk installation, and recognition rates **have not been tested in this environment**. Do the acceptance test on actual hardware.
- If the Pi has no internet, the browser libraries will not load. Speech-model inference remains locally computed once installed, but the app requires the JS dependencies to load.
