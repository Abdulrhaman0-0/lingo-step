"""Audio is optional; errors are surfaced rather than reported as success."""
import platform
import subprocess
import shutil
import threading

class SystemVoice:
    def __init__(self):
        self.command=shutil.which("espeak-ng") or shutil.which("espeak")
        self.platform=platform.system()

    def say_letter(self,letter):
        if len(letter)!=1 or not letter.isalpha(): raise ValueError("Invalid letter")
        if self.command:
            subprocess.Popen([self.command,"-v","en","-s","105",letter],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        elif self.platform == "Windows":
            # Windows built-in speech engine; no pip dependencies.
            safe=letter.upper()
            script=("Add-Type -AssemblyName System.Speech; "
                    "$v=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    "$v.Speak('"+safe+"')")
            subprocess.Popen(["powershell","-NoProfile","-Command",script],
                             creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        elif self.platform == "Darwin":
            subprocess.Popen(["say",letter])
        else:
            raise RuntimeError("Install espeak-ng: sudo apt install espeak-ng")
