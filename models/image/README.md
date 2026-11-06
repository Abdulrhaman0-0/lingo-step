# Image AI files (not yet provided)

Place **real exported** `model.tflite` and `config.json` here. Do NOT commit a pretend model.

The label order MUST exactly match the neural network output order. If you exported a
Teachable Machine Keras model, convert it separately on a desktop machine and verify
preprocessing and label ordering against the original model. Never assume the conversion
or accuracy is correct without testing it. `config.example.json` is an **example only**.

The adapter expects input `NHWC` and outputs class scores. Check whether your model
uses float32 normalization, uint8, int8 or softmax. Scores are treated as confidence;
**do not use logits as probabilities**. The current adapter requires score-style output.

If model is absent, all image recognition is unavailable; no fake predictions are used.
