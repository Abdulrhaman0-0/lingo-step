"""Audio is optional; errors are surfaced rather than reported as success."""
import platform
import subprocess
import shutil
from pathlib import Path

class SystemVoice:
    def __init__(self):
        self.command=shutil.which("espeak-ng") or shutil.which("espeak")
        self.platform=platform.system()
        self.process = None

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=2)
        self.process = None
        if self.platform == "Windows":
            import winsound
            winsound.PlaySound(None, 0)

    def say_feedback(self, key):
        if key not in ("correct", "retry", "retry_again"):
            raise ValueError("Unknown feedback sound")
        clip = Path(__file__).resolve().parents[2] / "assets" / "audio" / (key + ".wav")
        if not clip.is_file():
            raise FileNotFoundError("Missing feedback audio: " + str(clip))
        self.stop()
        if self.platform == "Windows":
            import winsound
            winsound.PlaySound(str(clip), winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            player = shutil.which("afplay" if self.platform == "Darwin" else "aplay")
            if not player:
                raise RuntimeError("Install alsa-utils to play feedback audio")
            args = [player, str(clip)] if self.platform == "Darwin" else [player, "-q", str(clip)]
            self.process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def say_letter(self,letter):
        if len(letter)!=1 or not letter.isalpha(): raise ValueError("Invalid letter")
        self.stop()
        if self.command:
            self.process = subprocess.Popen([self.command,"-v","en","-s","105",letter],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        elif self.platform == "Windows":
            # Windows built-in speech engine; no pip dependencies.
            safe=letter.upper()
            script=("Add-Type -AssemblyName System.Speech; "
                    "$v=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    "$v.Speak('"+safe+"')")
            self.process = subprocess.Popen(["powershell","-NoProfile","-Command",script],
                             creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        elif self.platform == "Darwin":
            self.process = subprocess.Popen(["say",letter])
        else:
            raise RuntimeError("Install espeak-ng: sudo apt install espeak-ng")
