# التدقيق الشامل وتقوية نظام Receipt-and-delivery

**تاريخ التقرير:** 26 أغسطس 2026
**النطاق:** Backend/FastAPI وSQLAlchemy، واجهة Vue/Vite/Pinia، تطبيق PySide6/SQLite، المزامنة Offline-first، الاستعادة والنسخ الاحتياطي، الإقلاع والأداء، CSP وCI/CD، وسلامة سلسلة الحيازة.

> هذا التدقيق ساكن وديناميكي محدود داخل بيئة اختبار محلية. لم تُنفّذ محاولات اختراق ضد بيئة إنتاج أو حسابات حقيقية، ولم تُلمس قواعد بيانات المستخدم الفعلية أو تُرسل بيانات إلى خدمة خارجية.

## الملخص التنفيذي

أُجري التدقيق قبل إضافة ميزات specimen أو Android أو تكاملات الأجهزة واسعة النطاق، لأن سلامة البيانات والمزامنة والاستعادة أولوية أعلى. أظهرت المراجعة أن أساس التطبيق يعمل ويملك تغطية اختبار واسعة، لكن بعض الضمانات المهمة كانت أضعف من متطلبات نظام Offline-first لسلسلة الحيازة. عولجت خلال هذه الدورة المشكلات القابلة للإصلاح منخفضة المخاطر، بينما سُجلت القرارات التي تحتاج ترحيلًا معماريًا أو تشغيليًا صريحًا بدل إدخال تغييرات صامتة.

| المجال | النتيجة الحالية | مستوى الثقة | الإجراء في هذه الدورة |
|---|---|---:|---|
| جلسة الويب | Cookies محمية وCSRF، مع بقاء Bearer لمسار التوافق القديم | مؤكد | مراجعة CSP وتثبيت حدود WebSocket موثقة سابقًا |
| المزامنة | منع overwrite الصامت، deduplication محلي، branch scoping في pull، وحدود payload | مؤكد | تقوية Backend وdesktop وإضافة اختبارات |
| البيانات | partial item update كان قد يحقق حالة غير متسقة بعد دمج غير صالح | مؤكد | إضافة merged validation قبل mutation/commit |
| الاستعادة | النسخة كانت تُتحقق بسلامة SQLite فقط دون checksum دائم، والاستبدال لم يكن ذريًا | مؤكد | SHA-256 وSQLite backup إلى ملف مؤقت ثم `os.replace` |
| migrations | desktop يملك migrations محلية متسلسلة؛ Backend ما زال يعتمد `create_all` | مؤكد | إضافة ADR، دون الادعاء بأن production migration اكتملت |
| عزل المؤسسات | User في Backend لا يملك tenant/organization scope شاملًا | مؤكد | تسجيله كخطر معماري؛ لم يُضف filter جزئي خطير |
| الأداء | القياسات المحلية أقل بكثير من الأهداف في benchmark محدود | مقاس جزئي | إنشاء baseline؛ لا يوجد ادعاء بأداء إنتاجي أو UI كامل |

## المنهجية وحدودها

جُمعت الأدلة من مصدر الشيفرة واختبارات المشروع وقياسات محلية معزولة. شملت الفحوصات مسارات المصادقة والـRBAC والمرفقات وWebSocket والمعاملات والمزامنة وقاعدة SQLite والاستعادة، إضافة إلى lint وفحوصات الاعتماديات الموجودة في خط العمل. لا تُعد نتائج الاختبارات المحلية اختبار اختراق، ولا تثبت سلامة إعدادات TLS أو DNS أو WAF أو النسخ الاحتياطي خارج الجهاز.

الخطر الأهم في تفسير التقرير هو الخلط بين «وجود كود أو schema» وبين «تحقيق الضمان في كل مسار». لذلك صُنفت النتائج إلى مؤكد، خطر/قرار مؤجل، ونتيجة سلبية كاذبة أو غير قابلة للإثبات. المراجع الأساسية هي خريطة الكود، طبقة المزامنة، schema المحلي، وخدمة الاستعادة [1] [2] [3] [4].

## النتائج المؤكدة والإصلاحات

### 1. سلامة المزامنة وسلسلة الحيازة — عولج جزئيًا

كانت خدمة Backend تبحث عن سجل سابق حسب entity ثم تسمح بمنطق قريب من last-writer-wins، كما كان pull يتجاهل branch في الاستعلام. هذا غير مناسب لسجل custody أو receipt لا يجوز فيه إسقاط النسخة الأقدم لمجرد وصول نسخة أحدث. أصبح push يتحقق من نوع العملية وentity وJSON serialization وحد 5 MB للـpayload، ويقارن النسخة الموجودة داخل الفرع نفسه. أضيف `idempotency_key` إلزامي إلى SyncEntry وحُفظ في SyncLog مع unique partial index؛ التكرار المطابق يُعد idempotent، أما إعادة استخدام المفتاح مع بيانات مختلفة أو تكرار entity بمفتاح جديد فيُعاد كتعارض يحتاج مراجعة ولا يُستبدل payload الأصلي.

على desktop أصبح كل عنصر في `sync_queue` يملك مفتاح idempotency محليًا افتراضيًا، مع unique partial index للمفاتيح غير الفارغة، وحد retry/backoff حتى ساعة، واحتفاظ بالـpayload عند conflict. أصبح `sync_all()` يرسل `idempotency_key` ويعالج `conflict_items` بدل تعليم كل العناصر كمزامنة ناجحة. كما أضيفت فلترة branch إلى pull في Backend وAPIClient. هذه الحماية تمنع overwrite الصامت داخل مسار المزامنة الحالي، لكنها لا تعني أن Backend صار نظام event store كاملًا؛ ما زالت migration PostgreSQL الرسمية مطلوبة لتطبيق العمود والفهرس على قاعدة منشورة، وفق ADR-002.

### 2. partial update لمجاميع العينات — عولج

كانت Pydantic تسمح بتعديل جزئي لحقول item، بينما كان التحقق يجري على الحقول الواردة وحدها لا على النتيجة المدمجة مع item الموجود. أضيف الآن بناء نسخة merged افتراضية تشمل العناصر الحالية والتحديثات والإضافات والحذف، ثم يُطبق `_validate_item_counts` قبل تغيير الكائنات أو تنفيذ commit. أضيف regression test يثبت أن تعديل `valid_count` وحده بما يجعل المجموع غير متطابق يعيد HTTP 422 ويحافظ على القيمة القديمة.

### 3. النسخ الاحتياطي والاستعادة — عولجت نقاط سلامة منخفضة المخاطر

أصبح كل backup جديد يحسب SHA-256 ويسجله في عمود `backups.checksum` بعد migration محلية v13. عند توفر checksum محفوظ، يقارن `verify_backup` البصمة قبل السماح بالاستعادة. ولتقليل احتمال فقد قاعدة البيانات عند انقطاع النسخ، تنفذ الاستعادة SQLite online backup إلى ملف مؤقت، تتحقق من الملف المؤقت، ثم تستخدم `os.replace` بدل نقل قاعدة البيانات الحالية ثم الكتابة فوق المسار مباشرة. وأصبح recovery snapshot يستخدم المسار المؤقت نفسه مع اسم يتضمن microseconds.

هذه الحماية لا تعوض تشفير النسخ أو تخزين نسخة خارجية موثوقة أو اختبار استعادة دوري. كما أن النسخ القديمة التي لا تملك checksum تبقى قابلة للتحقق من SQLite integrity فقط، ويجب ترقية سياسة الاحتفاظ تدريجيًا دون إعادة كتابة بيانات المستخدم صامتًا.

### 4. إقلاع desktop والمزامنة — عولج تجميد معروف دون نقل كل الإقلاع

ثبتت المراجعة أن `sync_pending` كان متصلًا مباشرة بـQTimer في خيط واجهة Qt، ولذلك يمكن لطلب HTTP أو عملية DB أن يحجز event loop. نُقل التنفيذ إلى `SyncWorker` و`QThread` مع منع تشغيل worker ثانٍ أثناء وجود الأول، وتُرسل النتيجة إلى status bar فقط. لم تُنقل `init_db` أو seeding أو diagnostics تلقائيًا إلى thread لأن ذلك يحتاج إدارة lifecycle وقواعد اتصال SQLite واختبارًا بصريًا منفصلًا.

القياس المعزول لا يثبت أن كل إقلاع Qt أقل من ثانيتين؛ فالـbenchmark يستبعد الرسم والـlogin وبناء صفحات الواجهة. لذلك بقيت هذه النقطة مصنفة «قياس جزئي»، مع baseline قابل لإعادة التشغيل في [5].

### 5. startup diagnostics والخصوصية — عولج اتصال خارجي غير لازم

لم يعد فحص الشبكة يتصل بجهة عامة افتراضية عند كل startup. لا يُنفذ الفحص إلا عند ضبط `LAB_API_HEALTH_URL` صراحة، مع قبول HTTP/HTTPS مطلق فقط. هذا يقلل telemetry غير المقصودة ويجعل انقطاع الإنترنت لا يؤثر في تشغيل التطبيق المحلي. لم تُضف OCR أو AI أو cloud integration تلقائية، ولم تُرسل بيانات مرضى أو tokens إلى الخارج.

### 6. الويب وCSP — تحسن دفاعي لا يلغي XSS

أضيفت توجيهات CSP وPermissions-Policy وCOOP/CORP إلى Nginx مع السماح المحدود بما تحتاجه الصور المحلية وblob workers وWebSocket. بقي `connect-src` متسعًا نسبيًا (`'self' https: wss:`) حتى لا ينكسر نشر API cross-origin الحالي؛ تضييقه إلى origins صريحة هو إجراء لاحق بعد حسم topology وCORS/cookie domain.

انتقال الويب السابق إلى HttpOnly access/refresh Cookies مع CSRF يمنع JavaScript العادي من قراءة JWT، لكنه **لا يجعل XSS مستحيلًا**. إذا نُفذت شيفرة خبيثة داخل origin الموثوق، فقد تنفذ طلبات باسم المستخدم لأن المتصفح يرسل Cookies تلقائيًا. لذلك تبقى CSP وتعقيم المدخلات وتجنب `v-html` غير الموثوق ضرورية [6].

## مخاطر مؤكدة لم تُغلق في هذه الدورة

| المعرف | الخطورة | الدليل | الأثر | الإجراء المطلوب |
|---|---|---|---|---|
| ARCH-001 | عالية قبل multi-facility | نموذج Backend User لا يفرض tenant/organization scope على كل الكيانات | احتمال وصول مستخدم مؤسسة إلى بيانات مؤسسة أخرى إذا استُخدم النظام كمنصة متعددة الجهات | تصميم tenant model، backfill، policy، وفحوصات عدم العبور قبل تفعيل multi-tenant؛ [ADR-001] |
| ARCH-002 | عالية تشغيليًا | `backend/app/db/session.py` يستخدم `Base.metadata.create_all` ولا توجد revision chain لـAlembic | تغييرات schema الإنتاجية قد تكون غير قابلة للتتبع أو rollback | اعتماد Alembic/نظام migrations PostgreSQL رسمي، ثم migration idempotency قبل production؛ [ADR-002] |
| SEC-011 | متوسطة | مسار `/api/v1` Bearer باقٍ لتوافق desktop/mobile | سطح توافق أوسع واحتمال استعمال المسار القديم من browser | عزله على host/client policy منفصل ثم ترحيل العملاء وإيقافه؛ لا يُستخدم من Vue browser |
| SEC-012 | متوسطة | local SQLite غير مشفر | سرقة ملف الجهاز قد تكشف بيانات التشغيل والمرفقات أو metadata | ADR وتقييم SQLCipher/تشفير الحقول وإدارة مفاتيح Windows؛ [ADR-003] |
| DATA-003 | متوسطة | `log_audit` ينفذ commit منفصلًا عن mutation في بعض الخدمات | قد تنجح business mutation ثم يفشل audit أو العكس، حسب المسار | جعل mutation وaudit في transaction واحدة حيث يمكن، أو outbox durable مع سياسة فشل صريحة |
| DATA-004 | منخفضة/متوسطة | custody unique idempotency race يحتاج اختبارًا متوازيًا فعليًا | duplicate concurrent request كان قد يرفع IntegrityError خامًا | عولج المسار بالتقاط IntegrityError وrollback وإعادة قراءة الحدث الفائز؛ يبقى اختبار race متعدد الجلسات ضمن hardening لاحق |
| OPS-001 | متوسطة | restore integrity محلي فقط، لا يوجد proof دوري لاستعادة نسخة مشفرة خارج الجهاز | قد يكتشف الفساد متأخرًا أو يفشل التعافي بعد فقد الجهاز | اختبار restore مجدول، retention خارج الجهاز، ومراقبة checksum/age |
| PERF-001 | منخفضة/متوسطة | تشخيص وseed وإعداد UI ما زالت قبل loop | أجهزة Windows ضعيفة قد ترى startup أطول من baseline المعزول | قياس Qt الحقيقي على Windows؛ نقل الأعمال غير الحرجة تدريجيًا مع QThread واتصالات مستقلة |

## مراجعة النتائج السلبية الكاذبة أو غير القابلة للإثبات

لم تعتبر المراجعة وجود `v-html` في الواجهة ثغرة تلقائيًا؛ الاستخدامات التي تمت مراجعتها كانت في معظمها SVG ثابتًا موثوقًا، بينما receipt HTML الديناميكي يستخدم escape helper. يلزم استمرار المراجعة عند إضافة قوالب جديدة، لكن لا يوجد من هذه الملاحظة وحدها إثبات injection.

كذلك لا يمكن اعتبار `HttpOnly` ضمانًا بإزالة XSS، ولا اعتبار وجود RBAC دليلًا على عزل المؤسسات، ولا اعتبار `create_all` نظام migration production، ولا اعتبار benchmark SQLite الصغير دليلًا على أداء آلاف السجلات أو عدم تجمد UI في كل أجهزة Windows. وأخيرًا لم تُختبر طابعات أو قارئات باركود أو NFC أو كاميرات فعلية في هذه الدورة، ولذلك لا يجوز وصفها بأنها تكاملات production-ready.

## سجل الفحوصات والاختبارات

أُعيدت الاختبارات المركزة ثم full suites بعد التغييرات. النتيجة النهائية قبل الدفع كانت: **Backend 74 passed**، و**desktop 1,578 passed**، و**frontend 24 passed** عبر 10 ملفات اختبار، مع نجاح Vite/PWA build. نجحت Ruff و`git diff --check`، ولم تُظهر Bandit نتائج medium/high، كما أظهر `pip-audit` عدم وجود ثغرات معروفة، وأظهر `npm audit --audit-level=high` عدد 0 vulnerabilities.

| الفحص | الغرض | حالة الدورة |
|---|---|---|
| Backend pytest | API، auth، transactions، custody، sync | **74 passed** |
| Desktop pytest | SQLite، recovery، sync، startup | **1,578 passed** |
| Frontend unit/build | Vue وVite/PWA | **24 passed / 10 files؛ build ناجح** |
| Ruff وdiff check | static lint وسلامة patch | ناجح |
| Bandit | فحص Python security patterns | لا medium/high؛ 25 low findings فقط |
| pip-audit/npm audit | ثغرات الاعتماديات المعروفة | 0 ثغرات معروفة / 0 vulnerabilities |

## خطة ما بعد التدقيق مرتبة بالأولوية

الأولوية الأولى هي اعتماد migrations Backend رسمية وtenant isolation قبل توسيع النشر متعدد المؤسسات. بعدها يجب استكمال transaction/audit atomicity وقياس race متعدد الجلسات، وتوفير conflict review UI لا يدفن النسخ المتعارضة. ثم يُعتمد تشفير SQLite والمرفقات مع إدارة مفاتيح قابلة للاستعادة، وتُجرى اختبارات restore على Windows وبيئة PostgreSQL staging. بعد ذلك فقط تُستأنف إضافات Android والأجهزة وOCR، على أن يكون OCR محليًا أو opt-in ولا يرسل PHI إلى خدمة خارجية دون موافقة صريحة.

## المراجع المحلية

[1]: ../../backend/app/services/sync_service.py "Backend SyncService"
[2]: ../../lab_system/app/sync/service.py "Desktop SyncService"
[3]: ../../lab_system/app/database/db.py "Desktop SQLite schema and migrations"
[4]: ../../lab_system/app/services/recovery_service.py "Recovery and backup verification"
[5]: ../performance/PERFORMANCE_BASELINE.md "Performance baseline"
[6]: ../SECURITY_AUDIT.md "Previous security audit and cookie/CSRF review"

## قرارات معمارية مرتبطة

[ADR-001]: ../adr/ADR-001-tenant-isolation.md "Tenant isolation before multi-facility"
[ADR-002]: ../adr/ADR-002-backend-migrations.md "Backend production migrations"
[ADR-003]: ../adr/ADR-003-local-data-encryption.md "Local database and attachment encryption"
