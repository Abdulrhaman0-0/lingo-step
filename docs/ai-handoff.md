# المطلوب من شات AI علشان نربط النموذج

## Image classifier

- Model files + export type (Teachable Machine Keras or TensorFlow.js etc.).
- `labels.txt` EXACT order; class names and count.
- Input dimensions / tensor dtype / color format / normalization.
- Output tensor (softmax probabilities or logits?) and validation accuracy.
- One real test card image per class plus negative examples, with privacy approval.

**Important:** TensorFlow.js `model.json` is not directly a `.tflite` file. Conversion
and parity testing must happen before using `TFLiteImageClassifier`.

## Audio classifier

- Actual exported model, microphone sample rate, audio duration, preprocessing,
  labels A–Z (or covered subset), noise robustness and validation metrics.
- A label prediction does not mean child pronunciation quality was evaluated.

## Integration contract

`predict(image) -> Prediction(label, confidence, source="real") or None`

`recognize_letter(audio) -> Prediction(label, confidence, source="real") or None`

Model imports cannot be silently replaced by guessed or mocked values.
