# نظام إدارة الاستلام المختبري (Desktop Native)

تطبيق مكتبي محلي بالكامل (Offline) مبني بـ **PySide6 + SQLite** لإدارة إيصالات ومعاملات المختبرات بأسلوب حكومي عراقي.

## الميزات
- تسجيل دخول محلي وصلاحيات (Admin/Supervisor/User/Auditor)
- إنشاء إيصالات مع ترقيم تلقائي بصيغة `LAB-YYYY-XXXXXX`
- حفظ عناصر العينات مع تحقق القاعدة: `total = valid + damaged + rejected + non-conforming`
- تدقيق غير قابل للتعديل (Audit Logs)
- تخزين مرفقات خارج قاعدة البيانات في `storage/attachments`
- بنية جاهزة للتوسعة (تقارير، طباعة، نسخ احتياطي، مزامنة مستقبلية)

## الهيكل
- `lab_system/app/ui`: واجهات PySide6
- `lab_system/app/database`: تهيئة SQLite والـ schema
- `lab_system/app/services`: منطق الأعمال
- `lab_system/app/printing`: توليد PDF باستخدام ReportLab + QR + Barcode
- `lab_system/storage`: receipts/attachments/exports/backups/temp
- `installer/LabReceipt.iss`: سكربت Inno Setup

## التشغيل
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## بيانات الدخول الافتراضية
- Username: `admin`
- Password: `Admin@123`

## بناء ملف تنفيذي
```bash
pyinstaller --noconfirm --onefile --windowed --icon=lab_system/assets/icons/app.ico main.py
```

## إنشاء المثبّت (Inno Setup)
1. ابنِ EXE عبر PyInstaller.
2. افتح `installer/LabReceipt.iss` في Inno Setup.
3. Compile لإنتاج `LabReceiptSetup.exe`.
