# ADR-002: اعتماد migrations رسمية لـBackend

**الحالة:** مطلوب قبل production schema changes
**التاريخ:** 26 أغسطس 2026

## السياق

تهيئة Backend الحالية تستدعي `Base.metadata.create_all(bind=engine)`، ولا توجد revision chain أو Alembic environment تُطبق تغييرات schema وتتحقق منها في PostgreSQL. هذا مناسب لتجهيز قاعدة اختبار جديدة، لكنه لا يسجل rename/drop/backfill أو يضمن ترتيبًا قابلًا للتكرار والرجوع.

## القرار

يجب اعتماد Alembic أو نظام migrations مكافئ قبل إضافة أعمدة إنتاجية للمزامنة أو tenant isolation أو تغييرات custody. تُراجع كل migration في CI على قاعدة فارغة وقاعدة fixture قديمة، وتُنفذ migrations في نشر staging قبل production. لا يُعتبر `create_all` migration production ولا تُخفى أخطاء schema داخل startup.

## العلاقة بالدورة الحالية

أضيفت migrations محلية desktop حتى v13 لأن SQLite desktop يملك آلية schema version خاصة به. هذا لا يرحّل Backend PostgreSQL تلقائيًا ولا يبرر إضافة `idempotency_key` durable إلى `sync_logs` قبل وجود migration رسمية. تقوية الخدمة الحالية تعتمد dedupe payload/entity/branch بصورة انتقالية، وتبقى بحاجة إلى migration backend عند اعتماد event id دائم.

## معايير القبول المستقبلية

يجب أن تحتوي المستودع على revision files، أمر upgrade/ downgrade موثق، فحص drift في CI، وrunbook للنسخ الاحتياطي والrollback. يجب اختبار uniqueness وbackfill وقيود foreign key تحت PostgreSQL فعلي أو staging مطابق، مع منع أي بيانات حساسة في fixtures.
