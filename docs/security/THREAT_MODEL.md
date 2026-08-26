# نموذج التهديد الأمني لنظام LabReceiptSystem

**الإصدار:** 1.0
**التاريخ:** 26 أغسطس 2026
**النطاق:** Backend/FastAPI، واجهة Vue، تطبيق Windows/PySide6، قاعدة SQLite المحلية، PostgreSQL، التخزين المرفقي، المزامنة، WebSocket، والجسر المحلي للأجهزة.

> يعتمد النموذج مبدأ **Zero Trust بين المؤسسات والأجهزة**: لا يُعد `facility_id` المرسل من العميل دليلًا على نطاق الصلاحية، ولا يُعد barcode وحده دليلًا على هوية المريض أو العينة.

## الأصول الحساسة

| الأصل | التصنيف | متطلبات الحماية |
|---|---|---|
| Patient identifiers وبيانات الطلب | Highly Sensitive | تقليل الجمع، صلاحية محدودة، تشفير، منع التسريب في logs/exports |
| Specimen identity وbarcode | Highly Sensitive | uniqueness، normalization، integrity، ربط بالطلب والمؤسسة |
| Chain of Custody | Highly Sensitive | append-only، idempotency، ترتيب أحداث، منع overwrite، audit hash |
| سجلات التدقيق | Sensitive/Highly Sensitive | append-only، hash chain، صلاحية Auditor/Admin، كشف العبث |
| بيانات المؤسسات والشحنات | Sensitive | tenant scoping، RBAC، تشفير النقل، audit |
| Credentials وsession tokens | Critical Secret | HttpOnly/Secure cookies للويب، OS credential store للسطح المحلي، rotation |
| Attachments وexports | Highly Sensitive | allowlist، hash، access control، quota، retention، عدم التنفيذ |
| مفاتيح التشفير وأسرار الاتصال | Critical Secret | خارج source code، secret manager/OS store، rotation، عدم logging |

## الجهات والافتراضات

| الجهة | القدرة المحتملة | الضابط الأساسي |
|---|---|---|
| Technician | إنشاء أو مسح عينة ضمن صلاحياته | risk-based validation وconfirmation |
| Reception | استلام وتسليم وتسجيل discrepancy | matching وdual approval عند المخاطر العالية |
| Courier | تحديث حالة النقل أو التسليم المصرح | device/facility scope وmanifest state machine |
| Facility Admin | إدارة مستخدمي مؤسسته وبياناتها | tenant policy، break-glass محدود، audit |
| Directorate Admin | نطاق مركزي متعدد المؤسسات | صلاحية صريحة ومراقبة وتدقيق إضافي |
| Auditor | قراءة audit والتقارير المسموح بها | read-only، watermark، export audit |
| System Admin | إدارة البنية والتشغيل | لا يُمنح وصولًا دائمًا إلى patient data |
| Unauthorized Local User | نسخ ملفات SQLite أو تعديل config | file permissions، encryption، device revoke |
| Malicious File | ملف مرفق يحاول استغلال parser أو execution | MIME/magic bytes، hash، quarantine، no-execute |
| Compromised Device | جهاز مسروق أو root/admin عليه | revoke، restricted mode، تشفير، key lifecycle |
| Network Attacker | اعتراض أو replay أو API abuse | HTTPS، cookies/CSRF، Bearer isolation، rate limits |
| Malicious Insider | مستخدم صحيح ينفذ عملية غير مشروعة | least privilege، reason/approval، immutable audit |

## حدود الثقة وقواعدها

| الحد | Authentication | Authorization | Validation | Encryption | Audit |
|---|---|---|---|---|---|
| User ↔ EXE/Android | login، session timeout، re-auth للعملية الحساسة | role + authenticated facility/device | كل input محليًا وخادميًا | OS secure storage، SQLite encryption مستقبلًا | login، state changes، overrides |
| EXE ↔ Local DB | local process boundary فقط؛ لا يُعد ثقة مطلقة | file ACL وDB lifecycle | constraints، integrity_check، schema version | SQLCipher/field encryption قيد التنفيذ المخطط | local audit hash chain |
| EXE/Android ↔ Cloud API | access/session credentials، device registration | user + device + facility + permission + ownership | Pydantic/domain/idempotency/risk rules | TLS، no tokens in URL | request/event audit |
| Browser ↔ API | HttpOnly access/refresh cookies + CSRF | RBAC وserver-side scope | schema، size، origin، rate limit | HTTPS/Secure cookies | auth and mutation audit |
| Browser ↔ WebSocket | access cookie + Origin | user permission and connection limit | origin/connection/message bounds | WSS | connect/disconnect/security events |
| Cloud API ↔ PostgreSQL | private network/service identity | DB role least privilege | FK/unique/check/transaction constraints | TLS at transport، encryption at rest | audit/event records |
| Cloud API ↔ Object Storage | workload identity أو signed scoped URL | transaction ownership وexpiry | extension/MIME/size/hash/quota | encryption at rest + TLS | upload/download/delete audit |
| EXE ↔ Hardware bridge | localhost token/device identity | allowed command + facility/device | command schema/timeouts | local channel؛ TLS عند التوسعة الشبكية | print/scan/NFC command audit |
| Facility ↔ Facility | لا ثقة ضمنية | tenant scope and explicit exchange | manifest signature/hash، event id | TLS، signed payload عند الحاجة | cross-facility event trail |

## التهديدات الرئيسية وتحليل المعالجة

| ID | التهديد | المسار | الأثر | الضوابط الحالية/المطلوبة |
|---|---|---|---|---|
| TM-01 | وصول مستخدم إلى مؤسسة أخرى | API query/report/sync | تسريب أو تعديل بيانات | tenant model مركزي مطلوب قبل multi-facility؛ لا يكفي client `facility_id` |
| TM-02 | سرقة token أو session | browser/local device | انتحال هوية | HttpOnly/CSRF/Ori­gin، timeout، revoke؛ XSS ما زال خطرًا للطلبات المصادق عليها |
| TM-03 | replay أو duplicate event | sync/custody/receive | تكرار استلام أو تغيير التاريخ | idempotency keys، unique constraints، quarantine، ACK بلا تطبيق مكرر |
| TM-04 | sync poisoning | جهاز مخترق يرسل payload | فساد سجل الحيازة | device registration/revoke، event schema، branch/tenant scope، server authority |
| TM-05 | forged specimen/barcode | إدخال barcode مصنوع | ربط عينة خاطئة بمريض | opaque ID + integrity data، matching، hard warning، لا PHI داخل QR |
| TM-06 | malicious attachment | upload/download | RCE أو DoS أو تسريب | allowlist/magic bytes/hash/size/quota/no-execute/scan عند توفره |
| TM-07 | local DB copy/tampering | stolen Windows profile | كشف أو تعديل البيانات | ACL، checksum/backup، تشفير SQLite والمرفقات قيد التقييم، audit verification |
| TM-08 | malicious insider/override | reject/correct/close | فقد ثقة السجل | reason، previous/new state، approval risk-based، audit append-only |
| TM-09 | network/API abuse | login/upload/report/sync | DoS أو brute force | timeouts، rate limits حسب IP/user/device/facility، WAF/proxy في الإنتاج |
| TM-10 | power loss أثناء mutation | desktop DB/backup/migration | half-record أو فقد | transaction boundaries، SQLite backup API، temp+atomic replace، chaos tests |
| TM-11 | compromised plugin | OCR/printer/NFC/camera | crash أو تنفيذ غير آمن | process/worker isolation، fallback يدوي/barcode، disable flag |
| TM-12 | admin break-glass إساءة استخدام | support/restore/admin | وصول واسع غير مراقب | reason/approval/duration/audit، redacted diagnostic mode |

## قواعد التصميم الإلزامية

كل عملية تغيّر domain state يجب أن تحدد atomic unit، وتكتب domain change وoutbox event في نفس transaction عندما يصبح outbox فعالًا. لا يعتمد النظام على current status وحده لإعادة بناء تاريخ العينة؛ الأحداث immutable، والتعارضات تحفظ نسختي local وremote في quarantine.

يجب أن يحسب server scope من authenticated context/device registration، ثم يطابق ownership وfacility والسياسة. أي mismatch في Patient ID أو Specimen ID أو Order أو Facility أو collection data ينتج **hard warning** ولا يسمح بقبول صامت. العمليات عالية المخاطر مثل reject وcancel وoverride وrestore تحتاج confirmation، وقد تحتاج شخصًا ثانيًا بحسب risk score لا لكل عملية.

لا يجب أن تحتوي QR/barcode على PHI. يمكن أن تحتوي identifier opaque مع integrity data أو توقيع عند الحاجة. عند إصدار label أو manifest نهائي، يجب حفظ version/hash/actor/time/device، وأي تصحيح ينشئ version أو event جديدًا بدل تعديل التاريخ القديم.

## ما تم وما لم يتم

تم تنفيذ أو تقوية cookies/CSRF، Origin للـWebSocket، حدود upload، مسارات الملفات، idempotency للمزامنة المحلية والخلفية، quarantine، branch scoping، backup checksum، وworker للمزامنة. لم يُدّعَ بعد اكتمال tenant isolation أو تشفير SQLite أو device certificate/public-key registration أو manifest signing؛ هذه تحتاج migrations واختبارات وقرارات تشغيلية مستقلة.

## مراجع المشروع

[1]: ../audit/COMPREHENSIVE_AUDIT.md "Comprehensive audit"
[2]: ../adr/ADR-001-tenant-isolation.md "Tenant isolation ADR"
[3]: ../adr/ADR-003-local-data-encryption.md "Local encryption ADR"
