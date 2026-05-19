# نظام إدارة الاستلام المختبري

تطبيق مكتبي حكومي عراقي **Native Desktop** مبني بـ **PySide6 + SQLite** ويعمل بالكامل دون إنترنت.

## الوظائف المنجزة
- تسجيل دخول محلي وصلاحيات (Admin/Supervisor/User/Auditor).
- إدارة المستخدمين (إضافة + عرض).
- إدارة مؤسسات ديناميكية عبر قاعدة البيانات.
- أنواع معاملات ديناميكية وأنواع عينات ديناميكية من جداول إعدادات.
- إنشاء إيصال رسمي مع ترقيم تلقائي `LAB-YYYY-XXXXXX`.
- تحقق إلزامي لمعادلة العينات قبل الحفظ.
- أرشيف إيصالات محلي مع بحث سريع.
- تدقيق Audit Logs غير قابل للتعديل.
- إدارة مرفقات خارج SQLite مع hash وضغط صور.
- PDF احترافي مع QR + Barcode وتوقيعات.
- نسخ احتياطي محلي.

## هيكل المشروع
- `lab_system/app/ui` واجهات النوافذ.
- `lab_system/app/database` تهيئة ومخطط SQLite.
- `lab_system/app/services` منطق الأعمال.
- `lab_system/app/printing` طباعة PDF.
- `.github/workflows/build.yml` بناء تلقائي ويندوز.
- `installer/setup.iss` إعداد مثبت Inno Setup.

## التشغيل المحلي
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## بيانات الدخول الافتراضية
- username: `admin`
- password: `Admin@123`

## بناء ملف تنفيذي
```bash
pyinstaller --noconfirm --onefile --windowed --icon=assets/icons/app.ico main.py
```

## إنشاء مثبت LabReceiptSetup.exe
1. أنشئ EXE أولاً عبر PyInstaller.
2. افتح `installer/setup.iss` عبر Inno Setup.
3. نفّذ Compile لإنتاج `LabReceiptSetup.exe`.
