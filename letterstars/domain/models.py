"""Plain data structures: no UI, hardware or ML dependencies."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

LETTERS = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

@dataclass(frozen=True)
class Prediction:
    label: str
    confidence: float
    source: str = "real"

@dataclass(frozen=True)
class Attempt:
    mode: str
    target: str
    observed: Optional[str]
    confidence: Optional[float]
    result: str
    timestamp: str

    @classmethod
    def make(cls, mode, target, observed, confidence, result):
        return cls(mode, target, observed, confidence, result,
                   datetime.now(timezone.utc).isoformat(timespec="seconds"))
