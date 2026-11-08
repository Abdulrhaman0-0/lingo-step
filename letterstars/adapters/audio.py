"""Audio is optional; errors are surfaced rather than reported as success."""
import platform
import subprocess
import shutil
from pathlib import Path
import os
import queue
import threading
import tempfile

class SystemVoice:
    def __init__(self):
        self.command=shutil.which("espeak-ng") or shutil.which("espeak")
        self.platform=platform.system()
        self.process = None
        self.audio_device = os.getenv("LINGOSTEP_AUDIO_DEVICE", "").strip()
        self._errors = queue.Queue()
        self._cancel = threading.Event()
        self._watcher = None
        self._lock = threading.Lock()

    def pop_error(self):
        try:
            return self._errors.get_nowait()
        except queue.Empty:
            return None

    def _start_job(self, job):
        self.stop()
        self._cancel = threading.Event()
        cancel = self._cancel
        def run():
            try:
                job(cancel)
            except Exception as exc:
                if not cancel.is_set():
                    self._errors.put(str(exc))
        self._watcher = threading.Thread(target=run, daemon=True)
        self._watcher.start()

    def _run_command(self, args, cancel):
        options = {"stdout": subprocess.DEVNULL, "stderr": subprocess.PIPE}
        if self.platform == "Windows":
            options["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        with self._lock:
            if cancel.is_set():
                return False
            proc = subprocess.Popen(args, **options)
            self.process = proc
        _, error = proc.communicate()
        with self._lock:
            if self.process is proc:
                self.process = None
        if cancel.is_set():
            return False
        if proc.returncode:
            detail = (error or b"").decode("utf-8", errors="replace").strip()
            raise RuntimeError(detail or f"Audio player exited with code {proc.returncode}")
        return True

    def _start(self, args):
        self._start_job(lambda cancel: self._run_command(args, cancel))

    def playback_command(self, clip):
        """Use the desktop sound server so its Bluetooth output is respected."""
        if self.platform == "Darwin":
            player = shutil.which("afplay")
            if player:
                return [player, str(clip)]
        elif self.audio_device:
            player = shutil.which("aplay")
            if player:
                return [player, "-q", "-D", self.audio_device, str(clip)]
        else:
            for name in ("pw-play", "paplay", "aplay"):
                player = shutil.which(name)
                if player:
                    return [player, "-q", str(clip)] if name == "aplay" else [player, str(clip)]
        raise RuntimeError("Install pipewire-bin (Bluetooth/desktop) or alsa-utils (ALSA playback)")

    def wait(self, timeout=15):
        """Used by the diagnostic CLI; UI playback remains nonblocking."""
        if self._watcher is not None:
            self._watcher.join(timeout)
            if self._watcher.is_alive():
                self.stop()
                raise RuntimeError("Audio playback timed out")
        error = self.pop_error()
        if error:
            raise RuntimeError(error)

    def stop(self):
        self._cancel.set()
        with self._lock:
            proc = self.process
            self.process = None
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
        if self.platform == "Windows":
            import winsound
            winsound.PlaySound(None, 0)

    def say_feedback(self, key):
        if key not in ("correct", "retry", "retry_again"):
            raise ValueError("Unknown feedback sound")
        clip = Path(__file__).resolve().parents[2] / "assets" / "audio" / (key + ".wav")
        if not clip.is_file():
            raise FileNotFoundError("Missing feedback audio: " + str(clip))
        if self.platform == "Windows":
            import winsound
            def play():
                winsound.PlaySound(str(clip), winsound.SND_FILENAME)
            self._start_job(lambda cancel: play() if not cancel.is_set() else None)
        else:
            self._start(self.playback_command(clip))

    def say_letter(self,letter):
        if len(letter)!=1 or not letter.isalpha(): raise ValueError("Invalid letter")
        if self.command and self.platform not in ("Windows", "Darwin"):
            # Generate English speech into a temporary WAV, then use the same
            # Bluetooth-aware player as feedback. Everything runs off the UI thread.
            def speak(cancel):
                with tempfile.TemporaryDirectory(prefix="lingostep-letter-") as tmp:
                    clip = Path(tmp)/"letter.wav"
                    if self._run_command([self.command,"-v","en","-s","105","-w",str(clip),letter], cancel):
                        self._run_command(self.playback_command(clip), cancel)
            self._start_job(speak)
        elif self.platform == "Windows":
            # Windows built-in speech engine; no pip dependencies.
            safe=letter.upper()
            script=("Add-Type -AssemblyName System.Speech; "
                    "$v=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    "$v.Speak('"+safe+"')")
            # PowerShell stays hidden because this is background speech.
            self._start(["powershell","-NoProfile","-WindowStyle","Hidden","-Command",script])
        elif self.platform == "Darwin":
            self._start(["say",letter])
        else:
            raise RuntimeError("Install espeak-ng: sudo apt install espeak-ng")
