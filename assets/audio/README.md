# Arabic answer feedback

Bundled, AI-generated Arabic recordings created with the AI Voice Generator
plugin (clear voice). Files are mono PCM16 WAV at 22050 Hz and play offline.
No voice-generation account or Python decoder is needed on the Raspberry Pi.
Clips are peak-normalized to 85% without clipping, with 600 ms of lead-in
silence and 200 ms at the end to reduce lost first syllables on Bluetooth
devices that need time to start streaming. This does not fix a muted or
misrouted speaker.

- `correct.wav`: ممتاز
- `retry.wav`: حاول مرة أخرى
- `retry_again.wav`: محاولة خاطئة، جرب ثانيةً

The first evaluated wrong answer uses retry; the second and subsequent wrong
answers use retry_again. Success, changing letter, selecting a child or opening
another activity resets the counter. Unrecognized audio/background frames do
not count as wrong answers. Feedback applies to both Learn and Revision.

Linux playback prefers `pw-play`, then `paplay`, so the desktop's selected
Bluetooth speaker is used. `aplay` is the fallback for hardware ALSA playback.
Setup includes the CLI players. Set `LINGOSTEP_AUDIO_DEVICE` only to force an
ALSA device; leave it unset for normal desktop/Bluetooth output.
English letter speech is generated to a temporary WAV and uses the same player.
Windows uses built-in winsound; macOS uses afplay. Playback errors are collected
in a worker and shown in the UI/Terminal instead of silently discarded.
Prompts stop before microphone recording starts, including pending synthesis.

Run `python scripts/check_audio.py` to play all three real clips sequentially,
or `python scripts/check_audio.py --list-devices` to inspect PipeWire outputs.
Player success does not prove the speaker was audible: check the selected
output, speaker volume, connection and mute state if playback is silent.
