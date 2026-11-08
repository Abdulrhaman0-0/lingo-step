# Test the complete A–Z + others image model

The filename is retained for existing links. The previous A–E demo has been
replaced by the supplied 27-class model (A–Z plus `others`).

## Windows PowerShell

From the project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-ui.txt
.\.venv\Scripts\python.exe -m pip install "numpy>=1.26,<3" "opencv-python>=4.8,<5" "ai-edge-litert>=1.4,<3" vosk sounddevice
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_image_model_runtime.py -v
.\.venv\Scripts\python.exe main.py
```

Vosk additionally requires the English language model in
models/speech/vosk-model-small-en-us-0.15, or LINGOSTEP_VOSK_MODEL pointing to it.

## Raspberry Pi 5

Use Raspberry Pi OS 64-bit Desktop. Transfer the updated project, or publish
it to GitHub before updating from there. From the project folder run:

```bash
bash setup_raspberry.sh
```

Setup installs/updates dependencies, downloads Vosk, checks both models and
opens the app. For later offline launches use `bash scripts/run_pi.sh`.

## Actual camera check

1. Select a child, then Revision. All targets A–Z must be supported.
2. Show each printed letter, including F and Z, with different angles/lighting.
3. Test wrong cards: stable confident wrong letters should request another try.
4. Show backgrounds/no card. Winning `others` predictions must request a stable
   card without recording an incorrect answer or awarding a star.
5. Compare preprocessing/predictions with the training export preview. Measure
   false positives and accuracy rather than treating confidence as accuracy.

Automated model inference on generated frames checks integration only; it does
not validate real camera accuracy or Raspberry Pi hardware.
