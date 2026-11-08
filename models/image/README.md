# LingoStep image model — A–Z + others

The user supplied the complete `converted_tflite.zip` on 2026-11-08.
`model_unquant.tflite` is installed as `model.tflite` (2,100,332 bytes).
`labels.txt` preserves the supplied output order: indices 0–25 are A–Z;
index 26 is `others`.

SHA256: `3f8c6e5f94a96888c73b7621cc86ef67d23e53d9d78d2c8011ab01187f512cf3`.

Keep model.tflite, config.json, labels.txt and the updated Python adapter together.
The adapter supports the 27-class model and still accepts older contiguous
letter-only models. If the highest output is `others`, inference returns no
letter, clears pending stable frames and records no revision attempt. It does
not substitute the second-highest class.

Expected float input: [1,224,224,3], output: [1,27]. The config uses RGB and
(pixel - 127.5) / 127.5 normalization. Confirm these settings against the
original training/export preview and measure accuracy using real printed cards,
lighting variations and background/no-card scenes. The presence of `others`
does not by itself prove how well unfamiliar inputs are rejected.

On Raspberry Pi OS 64-bit Desktop run `bash setup_raspberry.sh` to install
LiteRT/OpenCV and validate model loading. See docs/AE_MODEL_DESKTOP_TEST.md
for desktop checks; that filename is retained for existing links.
