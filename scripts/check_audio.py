"""Play the actual feedback WAVs and report playback errors instead of hiding them."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", help="ALSA output, e.g. plughw:CARD=Device,DEV=0")
    parser.add_argument("--list-devices", action="store_true")
    args = parser.parse_args()
    if args.list_devices:
        status = shutil.which("wpctl")
        if status:
            print("Desktop/PipeWire devices (including Bluetooth):", flush=True)
            return subprocess.call([status, "status"])
        player = shutil.which("aplay")
        if not player:
            raise RuntimeError("aplay not installed. On Raspberry run: sudo apt install alsa-utils")
        return subprocess.call([player, "-l"])
    if args.device:
        os.environ["LINGOSTEP_AUDIO_DEVICE"] = args.device
    from letterstars.adapters.audio import SystemVoice
    from letterstars.services.feedback import PHRASES
    voice = SystemVoice()
    print("Output:", voice.audio_device or "desktop default (select Bluetooth speaker in volume menu)", flush=True)
    if voice.platform not in ("Windows", "Darwin"):
        print("Player:", voice.playback_command(ROOT/"assets/audio/correct.wav")[0], flush=True)
    try:
        for key, phrase in PHRASES.items():
            print("Playing:", phrase, flush=True)
            voice.say_feedback(key)
            voice.wait()
            print("Player completed.", flush=True)
    finally:
        voice.stop()
    print("All files played without player errors. Confirm that you actually heard them.", flush=True)
    print("If silent: check speaker connection, mute/volume and output selection on the Pi.", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("AUDIO ERROR:", exc, file=sys.stderr)
        raise SystemExit(1)
