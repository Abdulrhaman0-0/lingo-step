# استبدال نموذج الحروف — ZIP بتاريخ 10 نوفمبر 2026

الملف الذي سلّمه الفريق: `4_6019569374568915343(1).zip`، ويحتوي `model_unquant.tflite` و`labels.txt`.

- الفئات: A–Z بالإضافة إلى `others`، أي 27 فئة.
- SHA-256 للنموذج الجديد: `61c70d1063d369dc2fc1625f941204938edd26b0aacccb237d8b8a92a4fea394`.
- النسخة الجديدة مختلفة عن ملف `models/image/model.tflite` الموجود في GitHub.
- **GitHub يحتوي حاليًا على سكربت الاستبدال فقط؛ ملف الـZIP الثنائي نفسه لم يتم رفعه إلى GitHub.** متحذفش النموذج الحالي قبل ما يكون معاك الـZIP نفسه.
- تم اختبار فكّ الملف وتركيب النموذج في مجلد محلي. **لم يتم اختبار inference أو الدقة الفعلية على الكروت والراسبيري**.

## خطوات تحديث الراسبيري

1. انقل الـZIP الحقيقي (مش صورة له) إلى `~/Downloads/` على الراسبيري.
2. أقفل تطبيق LingoStep، ثم افتح Terminal داخل سطح المكتب:

```bash
cd ~/lingo-step
git pull --ff-only origin main
.venv/bin/python scripts/install_image_model_zip.py "$HOME/Downloads/4_6019569374568915343(1).zip"
```

لو اسم الملف بدون `(1)`، عدّل الاسم داخل المسار. السكربت يراجع SHA-256 والـLabels **قبل** استبدال `models/image/model.tflite` القديم. لا يعدّل ملفات الصوت أو نماذج Vosk.

بعدها اختبر تحميله:

```bash
.venv/bin/python - <<'PY'
from letterstars.adapters.image_model import TFLiteImageClassifier
m = TFLiteImageClassifier("models/image")
print("READY:", m.ready, "ERROR:", m.error, "CLASSES:", len(m.labels))
PY
```

لازم يظهر `READY: True` و`CLASSES: 27`. بعد كده افتح البرنامج وجرب بطاقات حقيقية وحالات `others` وخلفيات مختلفة، وسجّل الدقة وزمن الاستجابة.

## التشغيل تلقائيًا بعد توصيل الكهرباء

```bash
bash scripts/install_autostart.sh --enable
sudo raspi-config
```

من قائمة `Boot / Auto Login` فعل `Desktop Autologin`، وبعدها `sudo reboot`. التفاصيل: [Autostart](AUTOSTART_RASPBERRY_AR.md).

**مهم:** تعديل النموذج على الراسبيري محليًا هيعمل تعديلًا في Git working tree. عند `git pull` مستقبلًا قد تحتاج حفظ النموذج في commit مقصود بعد مراجعته أو نسخه إلى مكان آمن، ولا تشغّل إعداد `setup_raspberry.sh` الذي يرفض التعديلات المحلية بدون مراجعتها.
