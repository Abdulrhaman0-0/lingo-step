# LingoStep — Final Delivery Checklist (2026-11-08)
**User-approved direction:** The child-facing product is a **native Python application** started with `python3 main.py` on Raspberry Pi 5 + touchscreen. **Only** the parent/guardian progress dashboard is a website. Do **not** replace the child app with a browser app.

## Reference designs
User-supplied images in chat on Nov 8: child app — welcome/create child, three-card home, learn screen, camera revision screen. Parent website — sign-in/child access, achievements and progress dashboard. Preserve ivory background, multicolour LingoStep logo, pastel stars, vivid blue/orange/yellow buttons, rounded tactile cards, Arabic RTL typography, touch-friendly navigation, 1280×900 reference canvas scaled to display.

## Deliverables and acceptance criteria
- [ ] **D01 — Native Python startup**: one `main.py` startup that uses final UI; no browser needed for child lessons.
- [ ] **D02 — Child profiles**: create/select an individual child profile and store a stable ID; never mix two children's attempts; use privacy-conscious identifiers.
- [ ] **D03 — Child UX**: welcome, home, Learn, Revision, Achievements; return/previous/next and Arabic feedback; letter A–Z; responsive touch-screen scaling; disable/indicate unavailable hardware gracefully.
- [ ] **D04 — Speak/listen**: speaker can pronounce current letter; microphone button asynchronously records speech, Vosk identifies *letter name* (not pronunciation quality), no fabricated confidences, errors surfaced.
- [ ] **D05 — Camera/image model**: USB webcam preview in native Python; real prediction through injected model adapter with confidence and stable frames; no pseudo predictions; make model formats/limits explicit.
- [ ] **D06 — Local progress**: SQLite per-child revision and learn attempt records (target, observed, result, timestamp, confidence), accurate summary and achievements from actual attempts; retains progress when offline.
- [ ] **D07 — Cloud sync contract**: queue unsynced attempt IDs and push over authenticated HTTPS when online, retry without loss, idempotent server ingestion; no voice recordings or child photographs uploaded; do not block UI during sync.
- [ ] **D08 — Separate parent web portal**: guardian authentication, child-specific dashboard inspired by supplied two web references; letters learned from completed attempts, progression, stars, achievements; no unauthenticated student data access.
- [ ] **D09 — Project structure/docs**: isolate UI / services / adapters / infrastructure / parent portal, hardware setup for Pi 5 Debian Trixie aarch64, executable setup/test instructions, gitpull workflow, no secrets committed.
- [ ] **D10 — Tests/checks**: unit tests for profiles/data isolation, progress logic, secure sync/auth, and UI headless rendering; run on CI; record untested real hardware/inference.
- [ ] **D11 — GitHub handoff**: develop safely on feature branch, create PR, preserve main until tested/approved, note every outstanding dependency and step to switch to main.

## Scope / limitations
- Image AI input supplied as Teachable Machine TFJS `model.json`, `weights.bin`, `metadata.json`; the existing native Python TFLite adapter cannot consume these unchanged. **Converting/exporting a tested TFLite model** (or implementing a verified native runtime) is still required before image inference works in Python. Never rename a TFJS file to `.tflite`.
- Vosk Python code can be integrated now; **Vosk English acoustic model** and tests with real USB microphone are pending.
- Parent cloud **deployment URL, domain/TLS, accounts and tokens** are not provided. Code can be developed and tested locally but cannot be called deployed/production-ready.
- Image classifier has only A–Z, **no NO_CARD class**; handle unknown confidence carefully; measure true accuracy rather than treating threshold as accuracy.
- No real-world Pi, VNC, touchscreen, webcam, speaker, microphone, or cloud integration tests can be honestly claimed without test results.

## Delivery progress log
- 2026-11-08: [done] Audit repository current `main` and initial AI-only feature branch; existing Tkinter/Pillow LingoStep UI is closest baseline.
- 2026-11-08: [in progress] Implement the deliverables on `feature/python-final-ui-cloud`. Update checkboxes only after code & tests substantiate completion.
