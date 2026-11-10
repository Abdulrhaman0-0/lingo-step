#!/usr/bin/env python3
"""Developer/CI only. Regenerate offline playback files; NOT run on Raspberry Pi."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
import wave

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "audio"

# Distinct text keys are preserved for compatibility with AnswerFeedback.
# Partial diacritics clarify articulation for Egyptian Arabic voice synthesis.
LINES = {
    "correct": "مُمْتاز!",
    "retry": "حاوِل مَرَّة أُخرى.",
    "retry_again": "خَطَأ، حاوِل مَرَّة أُخرى.",
}

def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)

def generate(voice="ar-EG-SalmaNeural", rate="-13%", pitch="+9Hz"):
    if not shutil.which("ffmpeg"):
        raise RuntimeError("Install FFmpeg on developer machine / GitHub runner first")
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lingostep-voice-") as temp:
        for key, phrase in LINES.items():
            raw = Path(temp) / (key + ".mp3")
            output = OUT / (key + ".wav")
            run(["edge-tts", "--voice", voice, "--rate="+rate, "--pitch="+pitch,
                 "--text", phrase, "--write-media", str(raw)])
            # Normalise dynamics, avoid sharp peaks and give Bluetooth a lead-in.
            run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y",
                 "-i", str(raw), "-af",
                 "loudnorm=I=-19:TP=-2.5:LRA=9,apad=pad_dur=0.3,adelay=550",
                 "-ar", "22050", "-ac", "1", "-c:a", "pcm_s16le", str(output)])
            with wave.open(str(output), "rb") as audio:
                assert audio.getnframes() > 5000 and audio.getnchannels() == 1
            print(f"Created {output.relative_to(ROOT)}")
    print("Ready for a human listening test. Do not call this measured voice quality.")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--voice", default="ar-EG-SalmaNeural")
    parser.add_argument("--rate", default="-13%")
    parser.add_argument("--pitch", default="+9Hz")
    args = parser.parse_args()
    generate(args.voice,args.rate,args.pitch)

if __name__ == "__main__":
    main()
