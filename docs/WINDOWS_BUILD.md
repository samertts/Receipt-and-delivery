# بناء نسخة Windows EXE

يحتوي المشروع على تطبيق سطح مكتب PySide6 مستقل، ويمكن إنتاج نسختين: ملف محمول `LabReceiptSystem.exe`، ومثبت Windows باسم `LabReceiptSetup.exe` عبر Inno Setup.

> لا يمكن الاعتماد على PyInstaller في Linux لإنتاج ملف Windows موثوق؛ ابنِ النسخة على Windows أو استخدم مهمة GitHub Actions التي تعمل على `windows-latest`.

## البناء على Windows

ثبّت Python 3.11 أو أحدث، ثم Inno Setup إذا أردت المثبت، وافتح PowerShell داخل مجلد المشروع:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\build_windows.ps1
```

ينفذ السكربت تثبيت المتطلبات، اختبارات تطبيق سطح المكتب، بناء EXE عبر `lab_system.spec`، ثم يبني المثبت إذا وجد `ISCC.exe`. عند غياب Inno Setup يظل ملف EXE المحمول صالحًا ويظهر تحذير بدل إيقاف العملية. تُكتب البصمات في `dist\SHA256SUMS.txt`.

## البناء عبر GitHub Actions

من تبويب **Actions** شغّل workflow باسم Windows Release يدويًا، أو ادفع tag يبدأ بـ `v` مثل `v1.3.0`. ينتج workflow artifacts باسمين واضحين للملف المحمول والمثبت، إضافة إلى checksums وmanifest وrelease notes. لا تُرفع نسخة release عامة إلا عند استخدام tag؛ التشغيل اليدوي يرفع artifacts داخل تشغيل workflow.

## تشغيل النسخة

بعد البناء، شغّل `dist\LabReceiptSystem.exe`. يخزن التطبيق قاعدة البيانات والمرفقات والنسخ الاحتياطية في `%LOCALAPPDATA%\LabReceiptSystem` بدل مجلد تثبيت البرنامج، لذلك لا يحتاج المستخدم صلاحيات Administrator للبيانات اليومية. يحتفظ إلغاء التثبيت بالبيانات المؤسسية وفق إعداد المثبت الحالي.

## الأجهزة والطباعة

نسخة EXE الحالية هي تطبيق سطح المكتب PySide6؛ ميزات الكاميرا والباركود وOCR وNFC الخاصة بواجهة الويب تبقى في `/devices`. للطابعة النظامية استخدم حوار الطباعة المعتاد، أما الطابعات الحرارية أو USB/Serial فتحتاج الجسر المحلي الاختياري الموثق في [DEVICE_INTEGRATION.md](../DEVICE_INTEGRATION.md). لا تُفتح منافذ الجسر على الشبكة ولا يُستخدم raw printing غير مصادق.

## التحقق بعد البناء

تحقق من وجود `LabReceiptSystem.exe`، راجع `dist\SHA256SUMS.txt`، ثم شغّل النسخة على حساب Windows عادي للتأكد من إنشاء مجلدات `%LOCALAPPDATA%`. اختبر تسجيل الدخول، إنشاء معاملة، إنشاء PDF، النسخ الاحتياطي، والطباعة قبل التوزيع المؤسسي.

## المراجع

[1] [PyInstaller Manual](https://pyinstaller.org/en/stable/)

[2] [Inno Setup Documentation](https://jrsoftware.org/isinfo.php)

[3] [GitHub Actions Windows runners](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners)
