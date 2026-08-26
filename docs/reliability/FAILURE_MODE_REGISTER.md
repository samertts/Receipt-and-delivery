# سجل أوضاع الفشل والاعتمادية

**الإصدار:** 1.0
**التاريخ:** 26 أغسطس 2026
**النطاق:** LabReceiptSystem desktop/backend الحالي، مع متطلبات التوسع إلى 40 مركزًا.

> يستخدم هذا السجل التفكير القائم على طرق الفشل: الاحتمال والأثر وقابلية الاكتشاف والاستعادة والوقاية والبديل. لا تعني العناصر التي تحمل حالة «مخطط» أن الضابط منفذ.

| ID | Subsystem | Failure | Cause | Impact | Detection | Prevention | Recovery | Fallback | Severity |
|---|---|---|---|---|---|---|---|---|---|
| REL-001 | Desktop startup | التطبيق لا يبدأ | DB تالفة أو config غير صالح | توقف العمل المحلي | startup diagnostics وerror ID | self-repair محدود وschema checks | restore snapshot موثوق | Safe Mode وexport diagnostics | High |
| REL-002 | SQLite transaction | نصف سجل بعد power loss | commit غير مكتمل أو kill أثناء mutation | بيانات غير متسقة | integrity_check واختبارات crash | transaction boundaries وFK/constraints | restore آخر backup ثم replay | إدخال pending محليًا | Critical |
| REL-003 | SQLite migration | migration تتوقف منتصفها | انقطاع طاقة أو lock contention | schema غير قابل للاستخدام | schema/migration history | backup قبل migration وlock | استعادة pre-migration backup | Safe Mode يمنع التشغيل العادي | Critical |
| REL-004 | SQLite WAL | WAL ينمو أو لا يُcheckpoint | process طويل أو file lock | disk exhaustion وبطء | قياس WAL size وdisk quota | checkpoint policy وعدم VACUUM أثناء الحرِج | checkpoint/maintenance | read-only restricted mode | Medium |
| REL-005 | Sync queue | عنصر عالق pending | network failure أو timeout | تأخر التحديث | queue health وretry counters | connect/read/total timeout وbackoff | retry آمن أو quarantine | export pending events | High |
| REL-006 | Sync queue | duplicate event | retry أو double scan | تكرار استلام أو audit | idempotency key/unique index | key لكل عملية | ACK أو mark idempotent | manual review إذا key reused | Critical |
| REL-007 | Sync conflict | نسخة remote تستبدل local | last-writer-wins غير مناسب | فقد تاريخ chain of custody | conflict_items وaudit | quarantine وحفظ local+remote | مراجعة معتمدة وإصدار correction | إبقاء المحلية pending | Critical |
| REL-008 | Sync scope | pull يعيد فرعًا آخر | branch من client أو query غير scoped | تسريب بيانات | negative branch tests | scope من authenticated context | revoke session وتحقيق audit | تعطيل sync | Critical |
| REL-009 | Backend schema | model تغيّر دون migration | create_all لا يطبق alteration | فشل runtime أو فقد constraint | `alembic check` وschema drift CI | Alembic revisions | backup وupgrade/rollback | منع deployment | Critical |
| REL-010 | PostgreSQL | deadlock أو lock contention | ترتيب locks مختلف أو batch ضخم | timeout أو فشل mutation | DB metrics وdeadlock logs | lock ordering وsmall transactions | rollback/retry محدود | queue job | High |
| REL-011 | API | request طويل بلا timeout | network/server stall | worker exhaustion وUI freeze | latency/timeout metrics | connect/read/total timeout | retry فقط للـ408/429/5xx/network | offline queue | High |
| REL-012 | Auth | session/token expired أثناء operation | idle timeout أو revoke | رفض متوقع أو lost action | 401/CSRF events | refresh flow وre-auth حساس | حفظ draft ثم re-auth | restricted mode | Medium |
| REL-013 | Device | جهاز مفقود أو revoked offline | سرقة أو compromise | sync poisoning بعد العودة | device status عند reconnect | device registration/revoke | force sync then restrict | local read-only/export | Critical |
| REL-014 | Attachment | ملف ضار أو كبير | extension spoof/disk exhaustion | RCE/DoS/leak | MIME/magic/hash/size/quota | allowlist وno-execute وscan | quarantine/delete authorized | reject upload | High |
| REL-015 | Attachment storage | DB commit يفشل بعد file write | ترتيب file/DB غير ذري | orphan files | reconciliation job | temp file ثم atomic rename | cleanup orphan بعد audit | retain quarantine | Medium |
| REL-016 | Backup | backup صحيح شكليًا لكنه tampered | نسخ يدوي أو disk corruption | restore غير موثوق | SQLite integrity + SHA-256 | checksum metadata وrotation | رفض restore وتحديد نسخة أخرى | snapshot سابق | Critical |
| REL-017 | Backup restore | الفشل يفسد DB الحالية | move/copy interruption | توقف أو فقد | post-copy integrity check | temp DB + atomic replace | restore pre-restore snapshot | Safe Mode | Critical |
| REL-018 | Backup retention | القرص يمتلئ | لا rotation/quota | توقف create/export | disk usage alert | daily/weekly/monthly policy | prune حسب policy بعد approval | read-only | High |
| REL-019 | Audit | business commit ينجح وaudit يفشل | commit منفصل | سجل غير مكتمل | audit chain verification | same transaction أو outbox | reconcile and alert | block sensitive op | High |
| REL-020 | Custody | transition غير صالح | state machine bypass أو race | تاريخ حيازة باطل | domain validation | explicit transitions + reason | correction event | quarantine | Critical |
| REL-021 | Identity matching | barcode/Patient/Order mismatch | manual error أو forged ID | عينة خاطئة | hard warning/matching layer | normalization + multi-field match | reject/dual approval | manual hold | Critical |
| REL-022 | Label/print | طباعة label خاطئ أو مكرر | wrong selection/retry | misidentification | print job ID/document hash | preview/confirmation/version | mark invalid ولا تحذف السجل | إعادة طباعة مع version | High |
| REL-023 | Hardware plugin | printer/NFC/camera/OCR crash | driver/plugin fault | UI أو process crash | worker exit/watchdog | process isolation وfeature flag | disable plugin/retry | manual input/barcode | High |
| REL-024 | Qt threading | worker يلمس UI أو DB connection غير آمن | ownership غير واضح | crash/deadlock/data race | thread assertions/logs | signals فقط وDB connection per worker | stop worker/restart | UI fallback | High |
| REL-025 | Job | import/report/sync job stuck | external I/O أو bug | backlog وذاكرة | job status/progress/watchdog | bounded worker pool وtimeouts | cancel/retry/recover | export job failure | Medium |
| REL-026 | Cache | status أو permission stale | TTL/invalidation ناقص | قرار خاطئ أو وصول غير صحيح | cache hit/age metrics | لا cache للصلاحيات/current state | invalidate and reload | direct DB read | High |
| REL-027 | Network | انقطاع أو packet loss | weak facility network | delayed sync | connectivity/queue metrics | offline-first وbackoff | replay ordered events | full local operation | High |
| REL-028 | API abuse | brute force/upload/report flood | malicious user/network | resource exhaustion | rate-limit metrics | limits حسب IP/user/device/facility | temporary block وalert | proxy/WAF limit | High |
| REL-029 | Tenant boundary | query بلا ownership scope | missing server context | cross-facility disclosure | cross-tenant negative tests | central authorization policy | disable multi-facility | central-only mode | Critical |
| REL-030 | Release | app/schema mismatch | rollout غير منسق | crash أو corruption | version/schema/device in diagnostics | compatibility matrix وchannels | rollback release + restore | pilot block | High |
| REL-031 | Logging | logs تكشف PHI/token | exception/details غير redacted | privacy incident | log review/DLP | structured redaction | rotate/restrict/delete by policy | disable verbose logs | High |
| REL-032 | Telemetry | جمع بيانات أكثر من اللازم | default-on telemetry | privacy/regulatory risk | config review | opt-in/configurable redacted metrics | disable and purge policy | no telemetry | High |
| REL-033 | Safe Mode | normal UI unavailable | plugin/config/schema issue | لا يمكن الإصلاح محليًا | startup failure count | minimal dependency path | DB check/restore/config repair | export diagnostic | High |
| REL-034 | Emergency Mode | cloud unavailable أثناء التسليم | server/network outage | توقف ميداني | health + offline indicator | local receive/search/scan/print/audit | force sync and reconcile | read-only if DB unsafe | Critical |

## تقييم الأولوية

العناصر الحرجة هي التي قد تغيّر أو تكشف chain of custody أو تمنع recovery: REL-002 و003 و006 و007 و008 و009 و013 و016 و017 و020 و021 و029 و034. يجب اختبارها في staging أو fixtures معطاة، لا ببيانات مرضى حقيقية. العناصر ذات الأولوية التالية هي disk exhaustion وdeadlocks وthread lifecycle وplugin isolation.

## خطة الاختبار والقياس

يجب أن تُبنى fixtures اصطناعية واقعية تشمل facilities وpatients المموهة وspecimens وtransfers وevents، ثم تُستخدم في اختبار 40 facility وconcurrent users وconcurrent sync وlarge manifests. يلزم تنفيذ chaos tests بقطع الشبكة والطابعة والكاميرا/NFC وقاعدة البيانات أثناء العمل، مع التحقق من عدم وجود half-record أو duplicate event.

لا يجوز اعتبار الأهداف الزمنية محققة دون قياس executable على Windows: بحث محلي نموذجي، event-loop latency، فتح 1,000 عنصر، نمو WAL، RSS، handles، threads، وحجم sync queue. baseline SQLite الحالي محدود وموجود في [PERFORMANCE_BASELINE.md](../performance/PERFORMANCE_BASELINE.md).

## عناصر منفذة حاليًا

تم تنفيذ أجزاء من REL-003 و005 و006 و007 و008 و009 جزئيًا و011 و016 و017 و024 الخاص بالمزامنة. لا يزال REL-001 Safe Mode الكامل و013 device revoke و019 audit atomicity و021 identity matching و022 print job governance و023 plugin process isolation و029 tenant isolation و034 Emergency Mode الكامل بحاجة إلى تنفيذ مستقل ومراجعة قبول.
