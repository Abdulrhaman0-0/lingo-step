# تشغيل LingoStep تلقائيًا على Raspberry Pi 5

ده تشغيل تلقائي **بعد تسجيل الدخول لسطح المكتب** على Raspberry Pi OS 64-bit Desktop. مناسب لتطبيق Tkinter، ومش هيشغل التطبيق قبل ما الشاشة الرسومية تجهز.

## أول مرة بعد تحديث المشروع

من Terminal على الراسبيري، **من غير sudo**:

```bash
cd ~/lingo-step
git pull --ff-only origin main
bash scripts/install_autostart.sh --enable
bash scripts/install_autostart.sh --status
```

لو ظهر إن البيئة `.venv` ناقصة:

```bash
bash setup_raspberry.sh --no-run --skip-system-update --skip-git-update
bash scripts/install_autostart.sh --enable
```

## فتح التطبيق مباشرة بعد توصيل الكهرباء

لازم تفعّل الدخول التلقائي لسطح المكتب؛ من `sudo raspi-config` اختار **System Options → Boot / Auto Login → Desktop Autologin**. لاحظ إن الدخول التلقائي بيقلل حماية الجهاز محليًا، فخليه لجهاز المعرض المخصص والموجود في مكان آمن.

بعد كده:

```bash
sudo reboot
```

المتوقع بعد الإقلاع: سطح المكتب يفتح حساب المستخدم تلقائيًا، وبعدها برنامج LingoStep يظهر Fullscreen. لا يُشغّل Git update أو install وقت الإقلاع.

## لو التطبيق ما فتحش

```bash
tail -n 80 ~/lingo-step/data/logs/autostart.log
bash scripts/install_autostart.sh --status
```

جرّب تشغيله يدويًا من سطح المكتب:

```bash
cd ~/lingo-step
bash scripts/run_pi.sh
```

راجع شاشة اللمس والكاميرا والمايك وسماعة البلوتوث كل واحدة لوحدها؛ نجاح الإقلاع التلقائي لا يضمن توصيل البلوتوث.

## تعطيل التشغيل التلقائي

```bash
cd ~/lingo-step
bash scripts/install_autostart.sh --disable
```

التعطيل لا يمسح حسابات الأطفال ولا التقدم ولا إعدادات Cloud. يمكن الخروج من Fullscreen بـ Escape، وF11 للتبديل.

## ملاحظات

- تأكد إن المشروع في مجلدك الحقيقي. السكربت يحدد المسار تلقائيًا؛ مش بيفترض إن اسم المستخدم `pi`.
- بيتأخر 8 ثوانٍ قبل بدء الواجهة حتى تكون جلسة الصوت وأجهزة USB ظهرت. يمكن ضبط `LINGOSTEP_STARTUP_DELAY` اختياريًا.
- التفعيل للمستخدم الحالي فقط، وليس خدمة root أو systemd. استخدم نفس حساب سطح المكتب عند التفعيل.
- ده تصميم جاهز للتجربة؛ لابد من التحقق بعد Reboot فعلي على Raspberry Pi.
