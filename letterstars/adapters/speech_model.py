"""Speech recognition hook: separate from pronunciation-quality assessment.

An implementation must return a genuine Prediction(label, confidence).
"""
class UnavailableSpeechClassifier:
    def recognize_letter(self, audio):
        return None
