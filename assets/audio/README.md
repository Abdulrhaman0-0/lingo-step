# Arabic answer feedback

Bundled, AI-generated Arabic recordings created with the AI Voice Generator
plugin (clear voice). Files are mono PCM16 WAV at 22050 Hz and play offline.
No voice-generation account or Python decoder is needed on the Raspberry Pi.

- `correct.wav`: ممتاز
- `retry.wav`: حاول مرة أخرى
- `retry_again.wav`: محاولة خاطئة، جرب ثانيةً

The first evaluated wrong answer uses retry; the second and subsequent wrong
answers use retry_again. Success, changing letter, selecting a child or opening
another activity resets the counter. Unrecognized audio/background frames do
not count as wrong answers. Feedback applies to both Learn and Revision.

Linux playback uses `aplay` from `alsa-utils` (included by setup_raspberry.sh).
Windows uses built-in winsound; macOS uses afplay. Playback needs a configured
audio output. Prompts stop before microphone recording starts.
