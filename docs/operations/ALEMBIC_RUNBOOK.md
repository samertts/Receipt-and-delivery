# Alembic PostgreSQL Runbook

هذا الدليل يخص **Backend PostgreSQL فقط**. لا يُطبّق على SQLite الخاص بتطبيق Windows، الذي يملك schema/migration lifecycle مستقلًا.

## قبل أول نشر

أنشئ نسخة قابلة للاستعادة، وجرّب استعادتها على staging منزوعة الحساسية. تحقق من `DATABASE_URL` ونسخة PostgreSQL ونسخة التطبيق، ثم افحص schema الحالية مقابل `backend/alembic/versions/03e87da238c7_baseline_current_backend_schema.py`.

```bash
export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:5432/DB'
export ENVIRONMENT=staging
alembic -c backend/alembic.ini current
alembic -c backend/alembic.ini history
```

إذا كانت قاعدة staging مطابقة فعليًا للـbaseline، ضع revision baseline فقط:

```bash
alembic -c backend/alembic.ini stamp 03e87da238c7
```

لا تستخدم `stamp head` لقاعدة غير مطابقة. أنشئ قاعدة جديدة من الصفر واختبر `upgrade head` قبل استخدام baseline على بيئة قائمة.

## التغيير الخاص بـSyncLog

التغيير مقسم إلى مرحلتين متوافقتين:

| Revision | الغرض |
|---|---|
| `7b1f3f1c2a01` | إضافة `idempotency_key` nullable وتنفيذ backfill deterministic للسجلات القديمة |
| `8c2d4e5f6a02` | فرض NOT NULL وإنشاء unique partial index بعد اكتمال backfill |

في نافذة نشر متوافقة، يجب أن يدعم الإصدار القديم العمود الجديد أو أن تُنفّذ المرحلتان ضمن migration lock/maintenance window. بعد التطبيق:

```bash
alembic -c backend/alembic.ini upgrade head
alembic -c backend/alembic.ini current
alembic -c backend/alembic.ini check
```

## مراجعة SQL قبل التنفيذ

```bash
alembic -c backend/alembic.ini upgrade head --sql > /tmp/alembic-upgrade.sql
less /tmp/alembic-upgrade.sql
```

ابحث عن `DROP TABLE` و`DROP COLUMN` وعمليات إعادة تسمية غير ممثلة يدويًا. لا تطبق ملفًا مولدًا بـ`--autogenerate` دون مراجعة؛ migrations المرشحة تحتاج تعديلًا يدويًا.

## rollback

قبل كل release، سجل revision الحالية وأنشئ backup. في staging اختبر:

```bash
alembic -c backend/alembic.ini downgrade -1
alembic -c backend/alembic.ini upgrade head
```

في production لا تنفذ downgrade أعمى إذا كانت النسخة الجديدة كتبت بيانات لا يمكن عكسها. أوقف rollout، استعد backup أو نفذ forward-fix، ثم سجل القرار في incident/change record.

## قفل migration والنشر

يجب أن يشغّل migration job واحد قبل تشغيل التطبيق. `backend/start.sh` يطبق `upgrade head`، ويجب أن يكون deployment controller مسؤولًا عن منع تشغيل نسخ متعددة متزامنة أو استخدام PostgreSQL advisory lock المطبق في `env.py`. لا يبدأ التطبيق على schema جزئية إذا فشلت migration.

## قنوات الإصدار

افصل `development` و`test` و`pilot` و`production` في secrets وDATABASE_URL وfeature flags. لا تستخدم بيانات مرضى حقيقية في development أو CI أو screenshots. لا تضع كلمات المرور أو URLs الحاوية على secrets في `alembic.ini` أو logs.

## قبول التغيير

يقبل Pull Request الخاص بالـmigration فقط إذا نجح `alembic upgrade head` من قاعدة فارغة، و`alembic check`، وdowngrade/upgrade cycle على fixture، وoffline SQL review، واختبارات Backend. اختبار PostgreSQL الحقيقي ينفذ في GitHub Actions عبر service container؛ البيئة المحلية الحالية لا تحتوي Docker أو `psql`، لذلك لم تُجرَ جلسة PostgreSQL محلية في هذه الدورة.
