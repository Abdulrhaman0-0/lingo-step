# قياس Accuracy وResponse Time لموديلَي LingoStep

الأداة: scripts/benchmark_ai.py — تعمل على اللابتوب أو Raspberry Pi 5. لا تغيّر بيانات الأطفال ولا تحفظ أي صور أو صوت في الاختبار المباشر.

## الفرق بين القياسات

| | Camera / TFLite | Microphone / Vosk |
|---|---|---|
| Accuracy | Ground Truth مقابل توقع الحرف المقبول، مع اعتبار Unknown خطأ للحروف | اسم الحرف المنطوق الحقيقي مقابل التوقع المقبول، مع اعتبار Unknown خطأ |
| Inference (ms) | زمن تحليل Frame واحد بواسطة TFLite (يشمل preprocessing) | زمن معالجة الصوت بعد انتهاء التسجيل باستخدام Vosk |
| Response (ms) | من Enter حتى تحقق 5 إطارات متتالية ثابتة بثقة 0.80 مع فاصل 170ms تقريبًا بين Frames | من بدء تسجيل الصوت حتى انتهاء التعرف؛ يشمل مدة التسجيل 3 ثوانٍ |
| Other inputs | كارت غير موجود أو شيء مختلف، نحسب نسبة الرفض وحدها | صمت أو كلام غير متعلق بالحروف، نحسب نسبة الرفض وحدها |

توقيت Camera Response هو تقريب لمسار اتخاذ القرار في التطبيق وليس توقيتًا دقيقًا لعرض واجهة GUI / تشغيل الصوت / Cloud. إذا انتهت المهلة بدون نتيجة ثابتة فلا نسجل Response موجبًا؛ نسجل Elapsed حتى المهلة والمحاولة كفشل للحروف. لا تُساوي Vosk Confidence بالدقة الفعلية أو بتقييم النطق السليم.

## أولًا: اختبار سريع على Pi أو اللابتوب

بعد سحب آخر تحديث وتجهيز البيئة والموديلات:

    cd ~/lingo-step
    git pull --ff-only origin main
    .venv/bin/python scripts/benchmark_ai.py --help

1) ضع الكارت أمام الكاميرا واضغط Enter؛ الحروف تتوزع عشوائيًا. OTHER يعني كارت غير موجود أو صورة غير مرتبطة بالحروف.

    .venv/bin/python scripts/benchmark_ai.py camera --letters ABCDE --repeats 3 --others 3

2) في المايك، اضغط Enter ثم انطق اسم الحرف الإنجليزي مرة واحدة خلال التسجيل (3 ثوانٍ).

    .venv/bin/python scripts/benchmark_ai.py mic --letters ABCDE --repeats 3 --duration 3

بديل Windows PowerShell: استخدم .\.venv\Scripts\python.exe بدل .venv/bin/python في الأوامر. إذا احتجت مايكًا آخر، أضف --device 1 حسب رقم الجهاز الصحيح.

النتائج تُحفظ تلقائيًا داخل results/benchmarks/ في 4 ملفات لكل تشغيل: CSV تفصيلي + summary.json + summary.md + confusion.csv. يمكن إيقاف الاختبار بكتابة q قبل المحاولة التالية أو Ctrl+C.

## ثانيًا: اختبار كامل وفق شروط Capstone

يفضل تجارب مستقلة لم تُستخدم في تدريب أو ضبط النموذج: 10 تجارب على الأقل لكل حرف (260 محاولة)، و20 تجربة أخرى للصور/الأصوات غير المعروفة. استخدم عدة مسافات وإضاءات للكاميرا، ومتكلمين بالغين مختلفين للمايك. لا توقف الاختبار مبكرًا لأن الدقة بدت عالية، ولا تعدل الحدود على نفس بيانات الاختبار ثم تعتبرها Test مستقلة.

    .venv/bin/python scripts/benchmark_ai.py camera --letters ABCDEFGHIJKLMNOPQRSTUVWXYZ --repeats 10 --others 20
    .venv/bin/python scripts/benchmark_ai.py mic --letters ABCDEFGHIJKLMNOPQRSTUVWXYZ --repeats 10 --duration 3 --others 20

## ثالثًا: Test Dataset محفوظة ومستقلة لإثبات الدقة

أنشئ data/image-test.csv؛ الملفات المذكورة في path نسبية إلى مكان CSV:

    path,expected
    images/card_a_001.jpg,A
    images/card_b_001.jpg,B
    images/no_card_001.jpg,OTHER

ثم نفذ:

    .venv/bin/python scripts/benchmark_ai.py image-files --manifest data/image-test.csv

للصوت أنشئ data/speech-test.csv بملفات WAV بصيغة 16000Hz، Mono، PCM16:

    path,expected
    audio/adult_a_001.wav,A
    audio/adult_b_001.wav,B
    audio/silence_001.wav,OTHER

ثم نفذ:

    .venv/bin/python scripts/benchmark_ai.py speech-files --manifest data/speech-test.csv

تجارب الملفات المحفوظة تقيس Inference ولا تدعي قياس Camera/Mic/GUI Response الحقيقي.

## التقارير

    .venv/bin/python scripts/benchmark_ai.py report results/benchmarks/YOUR_FILE.csv

Letter Accuracy (%) = عدد محاولات الحروف الصحيحة / إجمالي محاولات الحروف × 100. أي Unknown أو خطأ عند إدخال حرف صحيح يدخل في المقام ويُعتبر فشلًا.

الـNegative / OTHER rejection نسبة منفصلة. التقارير تعرض Mean وMedian وP95 وMax بالألف من الثانية، وPer-letter Accuracy، وConfusion Matrix، وRaw top-1 accuracy.

لا تعتبر 80% تحققت حتى تظهر في اختبار مستقل موثق؛ ثقة 98% في توقع واحد ليست 98% Accuracy. احفظ وصف البيانات وعدد العينات، التوزيع، الإضاءة، المسافة، الميكروفون، موديل الـAI والإصدار، وظروف المعايرة. لا ترفع بيانات تعريف أطفال أو صوت/صور خاصة أو كلمات مرور إلى GitHub العام.

## مشاركة النتائج

بعد التشغيل ابعت لنا ملف *_summary.md وCSV لكل نموذج لنكتب Results حقيقية ونرسم Accuracy وLatency Charts. Speech model هو Letter Name Recognition، وليس Pronunciation Quality Assessment.
