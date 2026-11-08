# Salma Smart Alphabet Learning — prototype starter

## Scope and limitations
- Five English letter names A–E (extend in config.json). USB webcam, USB microphone, screen, speaker.
- Speech is decoded by **pretrained Vosk offline ASR**. Speech-to-text is NOT phonetic/clinical pronunciation scoring. Single-letter names are difficult for speech recognizers; low-confidence/unknown results are retries, not evidence of a child's ability.
- Card reading uses **Tesseract OCR** (pretrained recognition) on a cropped camera frame, not a custom-trained classifier. Large BLACK capital letters on WHITE cards work best. It cannot reliably read cluttered handwriting or tiny/angled letters.
- Optional ThingSpeak Wi-Fi upload sends only mode, verdict, and response time; never raw recordings or pictures. Set API key in environment, never in source code.
- This app is a starter and **has not been tested with the team's actual hardware**. Do not claim 80%+ accuracy until measured on separate test examples.

## Raspberry Pi installation (Raspberry Pi OS Desktop, Debian-based)
1. Install OS with Raspberry Pi Imager, configure Wi-Fi, boot and update:
   \`sudo apt update && sudo apt upgrade -y\`
2. Connect USB webcam, USB mic, HDMI display, USB or HDMI audio speaker.
3. Install packages:
   \`sudo apt install -y python3-venv python3-tk espeak-ng tesseract-ocr libportaudio2 python3-opencv python3-pyaudio v4l-utils alsa-utils\`
4. From this directory: \`python3 -m venv --system-site-packages .venv\`
   \`. .venv/bin/activate\`
   \`python -m pip install -r requirements.txt\`
   (If pip builds OpenCV slowly, delete \`opencv-python\` from requirements.txt and use \`python3-opencv\` from apt.)
5. Download and unzip the **small English Vosk model** from https://alphacephei.com/vosk/models into this directory, renaming its extracted folder to \`model\`.
6. Check microphone \`arecord -l\`, playback \`speaker-test -t wav -c 2\`, webcam \`v4l2-ctl --list-devices\` and preview with \`ffplay /dev/video0\` if ffplay is available.
7. Run: \`python app.py\`

## Camera Module alternative
Current implementation expects a **USB webcam** (OpenCV VideoCapture). For Raspberry Pi Camera Module use \`rpicam-hello\` to test and then replace \`recognize_card()\` capture code with Picamera2; install with \`sudo apt install python3-picamera2\`. Camera ribbon and connector vary with Pi version.

## Cloud (optional until configured)
1. Create a private ThingSpeak channel with numeric field1 (mode), field2 (verdict), field3 (seconds).
2. In the terminal: \`export THINGSPEAK_WRITE_KEY='YOUR_WRITE_API_KEY'\` then run \`python app.py\`.
3. Verify successful writes in your channel; local \`results.csv\` is the fallback. **ThingSpeak free channels have rate limits**, so space trials apart; log API errors and confirm uploads.

## Accurate testing and safety
- Prepare 10+ previously unseen card photos per letter, under varied angles and lighting (50+ total for five letters), independently label true answers, measure accuracy using \`eval_trials.csv\` and \`python evaluate.py\`.
- For speech, use 10+ attempts per target in a quiet space, independently label actual spoken letter based on human observation, and record Vosk predicted letter. **Do not test children or claim support for disabilities without supervision, permissions, and accessible design review.**
- For every trial record expected, predicted, latency, conditions, and any failure. The goal is 80% on independent validation, not a guaranteed result.
- Sound recording is temporary in memory; avoid sending names and raw speech to cloud. No unattended use with children. Moderate volume.
- For exhibition, keep a hard-copy team logbook and copies of datasets, tests, calibration notes, and model details.
