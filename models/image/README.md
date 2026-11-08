# LingoStep — Image AI demo (A–E only)

The user supplied converted_tflite.zip on 2026-11-08. It contains model_unquant.tflite (2,091,532 bytes) and labels.txt (0 A, 1 B, 2 C, 3 D, 4 E).

MODEL BINARY STATUS: The GitHub connector supports text files, but not direct uploads from this conversation for 2 MB binary model files. The binary model.tflite still needs one manual upload to GitHub.

Upload the supplied, renamed model.tflite to the models/image/ directory on GitHub main using Add file > Upload files. The repository already has config.json and labels.txt. Then git pull origin main to get all three files.

Expected folder:
    models/image/model.tflite
    models/image/config.json
    models/image/labels.txt

Model output: 5 classes A–E. Expected float input shape: [1,224,224,3]. Expected output shape: [1,5]. Config uses RGB and the conventional Teachable Machine (pixel-127.5)/127.5 normalization as a starting point; compare predictions to the original export before relying on it.

During this DEMO the UI still teaches A–Z, but image Revision only grades A–E. F–Z explicitly show unsupported (no false failed attempt is stored).

No NO_CARD class exists: blank/background predictions might be high-confidence. Measure actual error rate on printed cards and negative backgrounds.

Once the model has been trained for A–Z, update model.tflite and config.json labels together and rerun tests.

SHA256 of supplied model_unquant.tflite: 8bf7f77225eef0fae24c221fe7921c6cd4d7dde426b0b69e0b87d6143b846021
