# استضافة موقع ولي الأمر على PythonAnywhere

التطبيق والموديلات يفضلوا على الراسبيري. الاستضافة تحتاج Flask وصفحات الموقع وقاعدة SQLite فقط.

## تجهيز الحزمة على جهاز التطوير

```powershell
.\.venv\Scripts\python.exe scripts/build_web_bundle.py
```

النتيجة `.venv/lingostep-web.zip`: ملفات مصدر محددة فقط، من غير بيانات طلاب أو مفاتيح أو موديلات.

## تجهيز حساب الاستضافة

1. حساب Beginner مجاني، وتأكيد البريد من المستخدم نفسه.
2. من Files ارفع الحزمة إلى مجلد الحساب.
3. افتح Bash console على PythonAnywhere ونفّذ، مع استبدال USERNAME باسم حسابك:

```bash
unzip -o ~/lingostep-web.zip -d ~
python3.13 -m venv ~/.virtualenvs/lingostep
~/.virtualenvs/lingostep/bin/pip install -r ~/lingostep-web/cloud/requirements-hosting.txt
~/.virtualenvs/lingostep/bin/python ~/lingostep-web/scripts/setup_hosted_web.py --url https://USERNAME.pythonanywhere.com
```

الأمر الأخير ينشئ المفاتيح مرة واحدة ويحتفظ بها. لا تطبعها ولا تشاركها. بيانات السيرفر موجودة في `~/lingostep-web/cloud/data/`؛ لا تمسح هذا المجلد عند تحديث الكود. ملف `pi-cloud-settings.json` داخله خاص لربط الراسبيري، ولا يحتوي مفتاح جلسات ولي الأمر.

4. من Web اختر Add a new web app → Manual configuration → Python 3.13.
5. اضبط Virtualenv على `/home/USERNAME/.virtualenvs/lingostep`، وSource/Working directory على `/home/USERNAME/lingostep-web`.
6. استبدل محتوى WSGI configuration بهذا النص:

```python
import sys
sys.path.insert(0, '/home/USERNAME/lingostep-web')
from cloud.pythonanywhere_wsgi import application
```

7. لو استخدمت Static files mapping: `/static/` إلى `/home/USERNAME/lingostep-web/cloud/static`.
8. فعّل Force HTTPS ثم Reload. افتح `/api/v1/health` على رابط الموقع وتأكد من `status: ok`، وافتح صفحة الدخول.

## توصيل الراسبيري — مرة واحدة

نزّل **بشكل خاص من حساب PythonAnywhere** ملف `cloud/data/pi-cloud-settings.json` وانقله إلى Downloads على الراسبيري. لا تضعه على GitHub أو داخل مجلد static عام، ولا ترسل التوكن في المحادثة.

بعد تحديث الريبو على الراسبيري، اقفل التطبيق ثم نفّذ:

```bash
cd ~/lingo-step
.venv/bin/python scripts/configure_cloud.py ~/Downloads/pi-cloud-settings.json
LINGOSTEP_MIC_DEVICE='USB PnP Sound Device' bash scripts/run_pi.sh
```

الإعداد يحفظ الاتصال في `data/cloud-settings.json` المستثنى من Git. عند تغيير الوجهة يعيد وضع المحاولات القديمة في طابور الإرسال؛ UUID يمنع مضاعفة النتائج. تسجيل الدخول للولي على الموقع المستضاف جديد ومنفصل عن حساب العرض المحلي، لكن تقدم الطفل الموجود على الراسبيري يظل محفوظًا ويُرفع عند المزامنة.

التشغيل اليومي بعد ذلك هو `bash scripts/run_pi.sh` مع اختيار الميكروفون المعتاد. لا تستخدم `run_demo.py` للاتصال بالموقع المستضاف لأنه يشغّل ويربط موقعًا محليًا مستقلًا عمدًا.

## اختبار العرض

جرّب حرفًا على الراسبيري، ثم ادخل الموقع من الموبايل، واعمل حساب ولي أمر واربط الطفل بالكود ذي الثماني خانات. حدّث الصفحة بعد المزامنة وتأكد من النتائج. لو فشل الرفع، افحص الاتصال و`CloudSync.last_error` وإعداد التوكن. الخطوة الفعلية على الراسبيري لا يمكن اعتمادها بمجرد نجاح اختبار السيرفر.

الحساب المجاني يحتاج تجديد تفعيل الموقع من Web كل شهر. هذه استضافة بروتوتايب صغير؛ احتفظ بنسخة خاصة من قاعدة البيانات والمفاتيح قبل تعديل/نقل الحساب.
