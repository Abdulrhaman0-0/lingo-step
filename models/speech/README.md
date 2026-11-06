# Speech AI integration point

The first version intentionally does not recognize speech. The audio classification
team should provide: export format, model artifact, labels, preprocessing and
sample rate, confidence calibration, validation results and sample recordings.

Implement `SpeechModelPort.recognize_letter(audio)` in a NEW adapter and inject
it via `main.py`. Recognition of a letter's name is NOT pronunciation scoring.
