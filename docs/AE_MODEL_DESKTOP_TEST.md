# Test the A–E image model locally (Windows first, Raspberry Pi second)

Repository: https://github.com/Abdulrhaman0-0/lingo-step (public; no credentials needed to clone).

1. Upload the real binary file model.tflite (2,091,532 bytes) to models/image/ in the GitHub main branch. config.json and labels.txt are already committed. On a different branch, commit to that branch first and merge before pulling main.
2. On Windows PowerShell:

    git clone https://github.com/Abdulrhaman0-0/lingo-step.git
    cd lingo-step
    py -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements-ui.txt
    .\.venv\Scripts\python.exe -m pip install numpy opencv-python tensorflow
    .\.venv\Scripts\python.exe main.py

3. Expected startup: welcome screen, child profile, Learn, Revision, Progress. A–E camera inference is enabled only when the real binary model and a working LiteRT/TensorFlow interpreter are installed; F–Z are NOT trained.
4. Test A–E printed flashcards, with the USB webcam pointed toward the card, vary lighting and angle. Negative/no-card input is not a learned class and must not be used as an accuracy benchmark.
5. For speech recognition add vosk and sounddevice, and place an actual Vosk English model at models/speech/vosk-model-small-en-us-0.15. Vosk letter-name recognition is not pronunciation grading.

On Raspberry Pi 5:

    cd ~/lingo-step
    git pull --ff-only origin main
    bash scripts/setup_pi_native.sh
    .venv/bin/python main.py

If the interpreter raises an error, send the full terminal output. Do not rename a TensorFlow.js model.json to model.tflite.

**Status:** This is a 5-class integration demo pending genuine camera/inference verification and the final 26-class model.
