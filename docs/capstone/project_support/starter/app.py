"""Salma Capstone prototype: letter learning and card revision.
Uses Vosk offline ASR, Tesseract OCR, Tkinter, and optional ThingSpeak upload.
This is an engineering starter, not a clinical speech assessment tool.
"""
import csv
import json
import os
import queue
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

BASE = Path(__file__).resolve().parent
CONFIG = json.loads((BASE / 'config.json').read_text(encoding='utf-8'))
LETTERS = CONFIG.get('letters', list('ABCDE'))
RESULTS = BASE / 'results.csv'


def speak(text):
    """Voice feedback: requires apt install espeak-ng."""
    try:
        subprocess.run(['espeak-ng', '-s', '115', '-v', 'en', text], check=True, timeout=15)
    except (OSError, subprocess.SubprocessError) as exc:
        print('Audio unavailable:', exc)


def log_result(mode, target, prediction, verdict, latency):
    new = not RESULTS.exists()
    with RESULTS.open('a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        if new:
            writer.writerow(['timestamp_utc', 'mode', 'target', 'prediction', 'verdict', 'response_seconds'])
        writer.writerow([datetime.now(timezone.utc).isoformat(), mode, target, prediction, verdict, f'{latency:.3f}'])
    # Optional IoT: a private ThingSpeak channel; no raw voice/images transmitted.
    key = os.environ.get('THINGSPEAK_WRITE_KEY', '').strip()
    if key:
        try:
            import requests
            requests.post('https://api.thingspeak.com/update.json', data={
                'api_key': key,
                'field1': 1 if mode == 'speech' else 2,
                'field2': 1 if verdict == 'correct' else 0 if verdict == 'incorrect' else -1,
                'field3': round(latency, 3),
                'status': f'{mode}:{target}:{verdict}',
            }, timeout=5).raise_for_status()
        except Exception as exc:
            print('Cloud upload failed (local log saved):', exc)


def recognize_speech(model_folder):
    """Capture 3s audio and decode with offline Vosk; returns decoded string."""
    import sounddevice as sd
    from vosk import Model, KaldiRecognizer
    samplerate = 16000
    model = Model(str(model_folder))
    recognizer = KaldiRecognizer(model, samplerate)
    chunks = queue.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            print('Mic:', status)
        chunks.put(bytes(indata))

    with sd.RawInputStream(samplerate=samplerate, blocksize=8000,
                           dtype='int16', channels=1, callback=callback):
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            try:
                block = chunks.get(timeout=0.5)
            except queue.Empty:
                continue
            recognizer.AcceptWaveform(block)
    return json.loads(recognizer.FinalResult()).get('text', '').strip().lower()


# Vosk recognition of *isolated letter names* can be unreliable; this only
# scores recognisable words, and otherwise requests a retry (not a failure).
LETTER_ALIASES = {
    'A': {'a', 'ay', 'hey'},
    'B': {'b', 'bee', 'be'},
    'C': {'c', 'see', 'sea'},
    'D': {'d', 'dee'},
    'E': {'e', 'ee'},
}


def score_speech(target, transcript):
    words = set(transcript.lower().split())
    matches = [letter for letter in LETTERS if words & LETTER_ALIASES.get(letter, set())]
    if len(matches) != 1:
        return 'uncertain'
    return 'correct' if matches[0] == target else 'incorrect'


def recognize_card(camera_index=0):
    """Capture one frame with USB webcam, read printed uppercase character."""
    import cv2
    import pytesseract
    camera = cv2.VideoCapture(camera_index)
    try:
        if not camera.isOpened():
            raise RuntimeError('USB camera not found. Check /dev/video0.')
        for _ in range(8):
            ok, image = camera.read()
        if not ok:
            raise RuntimeError('Unable to capture frame')
    finally:
        camera.release()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    # Central region: position the printed letter here, on a plain background.
    roi = gray[height//4:3*height//4, width//4:3*width//4]
    roi = cv2.GaussianBlur(roi, (3, 3), 0)
    _, binary = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(binary, config='--psm 10 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    letters = ''.join(c for c in text.upper() if c.isalpha())
    return letters if len(letters) == 1 else ''


class App:
    def __init__(self, root):
        self.root = root
        self.target = LETTERS[0]
        root.title('Salma - Smart Alphabet Learning')
        root.geometry('760x550')
        root.configure(bg='#f4f8fc')
        tk.Label(root, text='Smart Alphabet Learning', font=('Arial', 26, 'bold'),
                 bg='#f4f8fc', fg='#17456e').pack(pady=15)
        self.letter_label = tk.Label(root, text=self.target, font=('Arial', 110, 'bold'),
                                     bg='#f4f8fc', fg='#167d8d')
        self.letter_label.pack()
        self.status = tk.StringVar(value='Choose a letter and press Listen.')
        tk.Label(root, textvariable=self.status, wraplength=680, font=('Arial', 17),
                 bg='#f4f8fc').pack(pady=12)
        bar = tk.Frame(root, bg='#f4f8fc')
        bar.pack(pady=10)
        for letter in LETTERS:
            ttk.Button(bar, text=letter, command=lambda x=letter: self.set_target(x)).pack(side='left', padx=8)
        actions = tk.Frame(root, bg='#f4f8fc')
        actions.pack(pady=16)
        self.buttons = []
        for label, action in [('Listen to letter', self.listen),
                              ('Speak & check', self.check_speech),
                              ('Show card & check', self.check_card)]:
            b = ttk.Button(actions, text=label, command=action)
            b.pack(side='left', padx=7, ipadx=8, ipady=10)
            self.buttons.append(b)
        tk.Label(root, text='Speak: microphone | Revision: place ONE uppercase card in camera center',
                 font=('Arial', 12), bg='#f4f8fc').pack(pady=20)

    def set_target(self, letter):
        self.target = letter
        self.letter_label.configure(text=letter)
        self.status.set(f'Current letter: {letter}')

    def listen(self):
        target = self.target
        self.status.set(f'Listen: letter {target}')
        threading.Thread(target=speak, args=(target,), daemon=True).start()

    def start_worker(self, mode):
        target = self.target
        for b in self.buttons:
            b.configure(state='disabled')
        self.status.set('Listening for 3 seconds...' if mode == 'speech' else 'Reading card...')
        threading.Thread(target=self.worker, args=(mode, target), daemon=True).start()

    def check_speech(self):
        self.start_worker('speech')

    def check_card(self):
        self.start_worker('card')

    def worker(self, mode, target):
        started = time.monotonic()
        try:
            if mode == 'speech':
                model_folder = BASE / CONFIG.get('vosk_model_dir', 'model')
                if not model_folder.is_dir():
                    raise RuntimeError(f'Missing Vosk model folder: {model_folder}')
                prediction = recognize_speech(model_folder)
                verdict = score_speech(target, prediction)
            else:
                prediction = recognize_card(int(CONFIG.get('usb_camera_index', 0)))
                verdict = 'correct' if prediction == target else 'incorrect' if prediction else 'uncertain'
            latency = time.monotonic() - started
            log_result(mode, target, prediction, verdict, latency)
            message = {'correct': 'Great job! Correct!', 'incorrect': 'Try another card or letter.',
                       'uncertain': 'I could not recognize that clearly. Try again.'}[verdict]
            self.root.after(0, self.finish, message, verdict, prediction)
        except Exception as exc:
            self.root.after(0, self.finish, f'Error: {exc}', 'error', '')

    def finish(self, message, verdict, prediction):
        self.status.set(f'{message}   Detected: {prediction or "not clear"}')
        for b in self.buttons:
            b.configure(state='normal')
        if verdict != 'error':
            threading.Thread(target=speak, args=(message,), daemon=True).start()


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
