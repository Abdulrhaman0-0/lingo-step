"""Pure comparison rules; safe to unit test without devices."""
from collections import Counter
from .models import Prediction


def decide(target, predictions, minimum_confidence=0.80, minimum_stable_frames=5):
    """Reject uncertain or flickering predictions.

    Count the last N *consecutive* labels and require every frame to
    meet threshold. There is no positive result from single frames.
    """
    window = list(predictions)[-minimum_stable_frames:]
    if len(window) < minimum_stable_frames:
        return "not_recognized", None
    if any(p.source != "real" or p.confidence < minimum_confidence for p in window):
        return "not_recognized", None
    labels = {p.label.upper().strip() for p in window}
    if len(labels) != 1:
        return "not_recognized", None
    label = next(iter(labels))
    if label not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" or len(label) != 1:
        return "not_recognized", None
    return ("correct" if label == target else "try_again"), label
