# STEM Capstone evidence and measurable requirements

From G12 Semester 1 2026/2027 challenge: at least 4 measurable requirements;
response time and accuracy are mandatory; at least 80% AI model accuracy evidenced;
datasets/rubric, sensor calibration, hardware, ICT/IoT/AI and wireless transfer to cloud.

## Proposed metrics (targets must be approved and measured)

1. **Image classification test accuracy** ≥80% on held-out, independently labelled cards.
2. **Response latency** camera-frame-to-feedback ≤2 s (proposal; measure p50/p95).
3. **Touch input success** ≥95% across 20 taps/target (proposal).
4. **Session save reliability** 100% over 30 controlled test attempts (proposal).

These are PROJECT TARGETS, **not actual measured results**.

## Method

- Split training vs held-out data by card/lighting/person as appropriate to avoid leakage.
- For each class, record support and confusion matrix, precision and recall.
- Measure time with `time.perf_counter()` around acquisition, inference, and feedback.
- Calibrate camera lighting, camera distance and focus; microphone noise baseline separately.
- Document samples that the model cannot recognize (`not_recognized`), rather than hide them.
- Test Wi-Fi/cloud upload separately after a cloud interface is designed.
- Collect anonymized attempts only; do not upload children's voice/images without consent.

## Test log template

| Date | Device | Input | Expected | Predicted | Confidence | Latency ms | Result |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
