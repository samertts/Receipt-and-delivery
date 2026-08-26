# مصفوفة تنفيذ متطلبات ملف Deep System Hardening

**التاريخ:** 26 أغسطس 2026
**المبدأ:** «منفذ» يعني وجود كود واختبار مناسبين في المستودع. «جزئي» يعني وجود أساس أو ضابط محدود. «مخطط» يعني أن التنفيذ يحتاج schema أو سياسة أو أجهزة/بيئة لا يجوز اختلاقها.

| مجموعة المتطلبات | الحالة | التنفيذ/الدليل |
|---|---|---|
| Failure modes والاعتمادية | منفذ توثيقيًا + جزئي برمجيًا | `docs/reliability/FAILURE_MODE_REGISTER.md` وسجل health/recovery وchecksum وatomic restore وoutbox |
| Threat model وtrust boundaries | منفذ توثيقيًا | `docs/security/THREAT_MODEL.md` مع auth/authz/validation/encryption/audit لكل boundary |
| Zero Trust بين المؤسسات | جزئي | branch scoping وRBAC موجودان؛ tenant/facility ownership المركزي يحتاج organization scope وmigration مستقلة |
| Specimen identity وpatient matching | أساس منفذ | `backend/app/domain/workflow_risk.py` يطبق normalization ومقارنة hard warning؛ ربطه بمسارات specimen/manifest ينتظر domain كاملًا |
| Two-person/risk approval | أساس منفذ | `RiskEngine` يقرر confirmation/dual verification بحسب الإشارات؛ UI وapproval persistence يحتاجان workflow schema |
| Preventive UX/confirmation/override | جزئي | تأكيدات وقوالب حالية؛ override audit وrisk-based UI الكامل يحتاج ربطًا بكل عملية حساسة |
| Emergency/Safe Mode | منفذ كطبقة policy | `OperationalModeService` وHealthCheck/Recovery/Support wizards؛ مسار UI مستقل كامل لم يُفتح افتراضيًا |
| Plugin failure isolation | منفذ جزئيًا | فشل التحميل يسجل metadata ويعطل plugin؛ process isolation للأكواد غير الموثوقة يحتاج subprocess contract |
| Process/thread/async boundaries | منفذ جزئيًا | SyncWorker وJobManager وtimeouts؛ hardware/OCR isolation الفعلي ينتظر adapters حقيقية |
| Job system/watchdog | منفذ | `JobManager` يدعم ID/status/progress/timestamps/error/retry/timeout/cancel؛ persistence بعد restart غير مفعّل |
| Idempotency/inbox/outbox | منفذ جزئيًا | durable sync idempotency في Backend وSQLite، وreceipt mutation + outbox event في transaction واحدة؛ event-sourced specimen replay ينتظر domain |
| Event ordering/replay/snapshots | مخطط | يحتاج event store canonical وversion/sequence وسياسة late events قبل إضافته للإنتاج |
| Audit tamper detection | منفذ جزئيًا | local hash chain وroot hash؛ root signing/remote anchoring غير مفعّل |
| Local DB tampering/encryption | جزئي/مخطط | integrity/checksum/ACL ومسار recovery؛ SQLCipher/key lifecycle في ADR مستقل ولم يُفرض صامتًا |
| Session/device security | جزئي | cookies/CSRF للويب، idle timeout وre-auth desktop؛ device registry/public key/revoke server يحتاج model/API |
| Attachment/document security | منفذ جزئيًا | allowlist/hash/size/path controls؛ antivirus sandbox وper-user/facility quotas تحتاج policy/storage deployment |
| Backup/DR/corruption/power failure | منفذ جزئيًا | SHA-256، SQLite online backup، temp+atomic replace، integrity checks؛ restore drills وRPO/RTO الإنتاجية تحتاج staging |
| Transaction/lock/deadlock/thread safety | جزئي | merged validation، advisory migration lock، worker boundaries؛ اختبار concurrency الحقيقي على PostgreSQL/Windows مطلوب |
| Master data/versioning/retention | جزئي | active/inactive وخدمات catalog موجودة؛ effective dates/retention governance يحتاج قرار الجهة المالكة |
| Export/print/label privacy | جزئي | PDF/Excel/Rx existing وprint layouts؛ print job ledger/hash/label invalidation يحتاج توحيد adapter |
| Manifest version/sign/cancel/partial/return/reroute/split/merge | مخطط | لا توجد حاليًا schema كاملة؛ لا تُضاف كحقول متفرقة لأنها تؤثر في chain of custody |
| Synthetic data/load/soak/stress/chaos | جزئي | benchmark SQLite معزول؛ generator وPostgreSQL/Windows load/soak/chaos pipeline يحتاج بيئة اختبار مخصصة |
| Startup degradation/database growth/log rotation | جزئي | baseline وstartup diagnostics وWAL/checks موجودة؛ قياس 10k/100k/1M على Windows ومراقبة طويلة مطلوبان |
| Migration/release/rollback/feature flags | منفذ جزئيًا | Alembic scaffold وbaseline وexpand/backfill/enforce وCI gate وadvisory lock وfeature flags؛ production baseline يحتاج DB staging مطابقة |
| Telemetry/privacy/network/retries/rate limits/API compatibility | منفذ جزئيًا | telemetry opt-in redacted، API timeouts/retries، rate limiting وAPI v1 compatibility؛ telemetry transport/monitoring الخارجي غير مفعل |

## قرار التنفيذ

تم تنفيذ الأساسات منخفضة المخاطر التي يمكن اختبارها محليًا دون بيانات إنتاج أو أجهزة. العناصر المؤجلة ليست bugs مخفية؛ هي تغييرات مجال أو نشر تتطلب قرارًا مؤسسيًا، migrations إضافية، أو بيئة PostgreSQL/Windows فعلية. تشغيلها كـmock أو قبولها بلا اختبار سيزيد خطر فقد chain of custody بدل تقليله.


## تحديث أمني إضافي

تم استبدال `python-jose` بـ`PyJWT` عبر `backend/app/core/jwt_compat.py`، وتحديث `fastapi` إلى `0.141.1` و`python-multipart` إلى `0.0.31`. بعد التثبيت نجحت اختبارات Backend وعددها 79، ونتيجة `pip-audit -r backend/requirements.txt` أصبحت بلا ثغرات معروفة. لا يُعد ذلك بديلًا عن إعادة الفحص عند كل release.
