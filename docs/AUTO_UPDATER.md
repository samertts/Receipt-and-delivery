# نظام التحديث التلقائي لتطبيق LabReceiptSystem

## النتيجة الحالية

يحتوي تطبيق Windows على فحص تحديثات من داخل قائمة **مساعدة → التحقق من التحديثات**، مع تنفيذ العمل الشبكي في خيط خلفي حتى لا تتجمد الواجهة. كما يبدأ التطبيق، بعد ظهور الواجهة بثلاث ثوانٍ، فحصًا تلقائيًا واحدًا في الخلفية. لا يظهر أي مربع حوار إذا لم يوجد تحديث أو تعذر الاتصال، ويظهر الإشعار فقط عند العثور على manifest موثّق لإصدار أحدث. لا يبدأ التثبيت تلقائيًا بمجرد اكتشاف إصدار جديد؛ يراجع المستخدم رقم الإصدار وملاحظات الإصدار، ثم يوافق على التنزيل والتثبيت.

يقرأ التطبيق ملف `update.json` عبر HTTPS، ويتحقق من توقيع Ed25519 للبيانات قبل قبولها، ثم ينزّل مثبت Inno Setup إلى مجلد التحديثات الخاص بالمستخدم. بعد التنزيل يُعاد حساب SHA-256 ويُقارن بالقيمة الموجودة في manifest. لا يُستخدم `shell=True`، ولا يُقبل رابط HTTP، ولا يُشغّل المثبت قبل نجاح التحقق.

> **مهم:** لا تضع المفتاح الخاص في المستودع أو داخل EXE. المفتاح الخاص يُستخدم في CI فقط، بينما يُضمّن المفتاح العام في حزمة التطبيق.

## دورة الإصدار

| المرحلة | الإجراء |
|---|---|
| البناء | يبني Windows CI `LabReceiptSetup.exe` و`LabReceiptSystem.exe` عبر PyInstaller وInno Setup. |
| التوقيع | يقرأ CI `LAB_UPDATE_PRIVATE_KEY_B64` من GitHub Actions Secret ويولد `update.json` موقّعًا. |
| النشر | عند دفع tag مثل `v1.3.0` ينشر GitHub Release المثبت و`update.json` وملاحظات الإصدار. |
| الفحص | يفحص التطبيق تلقائيًا مرة واحدة بعد 3 ثوانٍ من بدء التشغيل، ويمكن الفحص يدويًا من قائمة المساعدة. يطلب التطبيق افتراضيًا `https://github.com/samertts/Receipt-and-delivery/releases/latest/download/update.json`. يمكن توجيهه إلى mirror داخلي عبر `LAB_UPDATE_MANIFEST_URL`، بشرط بقاء الرابط HTTPS وتوقيع manifest بالمفتاح العام المطابق. |
| التثبيت | بعد موافقة المستخدم، ينزّل المثبت، يتحقق من الحجم وSHA-256، ثم يشغله بدون shell ويغلق التطبيق. |

## إعداد المفاتيح مرة واحدة

أنشئ زوج Ed25519 على جهاز آمن لا يحتوي على المستودع العام. لا تُرسل المفتاح الخاص في المحادثة ولا تلتزم به في Git. مثال باستخدام Python ومكتبة `cryptography`:

```python
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

private = Ed25519PrivateKey.generate()
public = private.public_key()
print("PRIVATE:", base64.b64encode(private.private_bytes(
    serialization.Encoding.Raw,
    serialization.PrivateFormat.Raw,
    serialization.NoEncryption(),
)).decode())
print("PUBLIC:", base64.b64encode(public.public_bytes(
    serialization.Encoding.Raw,
    serialization.PublicFormat.Raw,
)).decode())
```

أضف قيمة `PRIVATE` إلى GitHub Actions Secret باسم `LAB_UPDATE_PRIVATE_KEY_B64`، وأضف قيمة `PUBLIC` إلى Secret باسم `LAB_UPDATE_PUBLIC_KEY_B64`. يكتب workflow المفتاح العام داخل `lab_system/app/update_public_key.py` مؤقتًا قبل PyInstaller. لا تسجل قيم المفاتيح في CI logs.

## إنشاء إصدار

غيّر ملف `VERSION`، حدّث `CHANGELOG.md`، ثم ادفع tag مطابقًا للنسخة:

```powershell
git checkout main
git pull --ff-only
git tag v1.3.0
git push origin v1.3.0
```

يتطلب إصدار موقّع وجود المفتاحين السريين السابقين. إذا لم يكن `LAB_UPDATE_PRIVATE_KEY_B64` موجودًا فسيفشل توليد `update.json` بدل نشر تحديث غير قابل للتحقق. أما البناء اليدوي على branch دون tag فيبقى صالحًا لبناء EXE للاختبار، لكنه لا ينشر manifest موقّعًا.

## اختبار محلي للmanifest

يمكن توليد manifest بعد بناء المثبت على Windows:

```powershell
$env:LAB_UPDATE_PRIVATE_KEY_B64 = "<private-key-base64>"
python scripts/generate_update_manifest.py `
  installer\Output\LabReceiptSetup.exe `
  --url "https://github.com/samertts/Receipt-and-delivery/releases/download/v1.3.0/LabReceiptSetup.exe" `
  --output update.json
```

يمكن اختبار worker داخل التطبيق دون تشغيل التثبيت الفعلي عبر اختبارات `tests/test_updater.py`. لا تستخدم رابطًا محليًا أو HTTP في إصدار production؛ الاختبار المحلي يجب أن يظل معزولًا ولا يُستخدم كقناة توزيع.

## التراجع والاسترداد

لا يحذف updater النسخة الحالية قبل تشغيل المثبت. إذا فشل التنزيل أو التحقق، يُحذف ملف `.exe.part` المؤقت ولا يُمس التطبيق. إذا فشل المثبت بعد تشغيله، يمكن للمستخدم إعادة تشغيل النسخة السابقة أو إعادة تثبيت artifact معروف من GitHub Release. قبل كل release احتفظ بالنسخة السابقة وملف checksums، ولا تحذف release قديمًا ما دامت هناك أجهزة لم تُحدّث.

## القيود الأمنية والتشغيلية

| الموضوع | القرار |
|---|---|
| القناة | HTTPS فقط للmanifest والمثبت. |
| الأصالة | Ed25519 للmanifest؛ private key خارج GitHub repository، وpublic key داخل الإصدار. |
| سلامة الملف | SHA-256 بعد التنزيل مع حد حجم أقصى 300 MB. |
| موافقة المستخدم | لا يوجد تثبيت صامت أو تحديث قسري من داخل التطبيق. |
| الصلاحيات | قد يطلب Inno Setup صلاحيات Administrator حسب إعداد المثبت الحالي. |
| المصدر | يعتمد updater على GitHub Releases العامة؛ للمستودعات الخاصة يجب استخدام قناة توزيع مصادق عليها بدل تضمين GitHub token في EXE. |
| توقيع Windows | توقيع Ed25519 هنا يثبت manifest؛ ولتقليل تحذيرات SmartScreen في التوزيع المؤسسي أضف لاحقًا Windows Authenticode certificate إلى EXE والمثبت. |

## بدائل مستقبلية

يمكن استبدال الوحدة الحالية بإطار WinSparkle للحصول على واجهة تحديث Windows أصلية مع appcast، أو استخدام TUFup عندما تصبح الحاجة إلى تدوير مفاتيح وأدوار metadata وتراجع رسمي أقوى. لا يُنصح بإضافة هذه التعقيدات قبل تثبيت سياسة إدارة المفاتيح والإصدارات.

## الملفات الأساسية

`lab_system/app/updater.py` ينفذ التحقق والتنزيل والتشغيل، و`lab_system/app/ui/app.py` يضيف worker وواجهة المستخدم، و`scripts/generate_update_manifest.py` يولد manifest موقّعًا، و`scripts/write_update_public_key.py` يجهز public key في CI، بينما `.github/workflows/build.yml` يربط البناء والنشر.
