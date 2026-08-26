# ملاحظات المصادر الرسمية لـAlembic

تمت مراجعة المصادر الرسمية التالية بتاريخ 26 أغسطس 2026:

1. https://alembic.sqlalchemy.org/en/latest/tutorial.html — يوضح أن بيئة Alembic تُنشأ مرة واحدة، وأن `env.py` يضبط الاتصال و`target_metadata`، وأن revisions تحفظ داخل شجرة المصدر.
2. https://alembic.sqlalchemy.org/en/latest/autogenerate.html — يوضح أن `--autogenerate` ينتج migrations مرشحة يجب مراجعتها يدويًا، وأنه لا يكتشف إعادة تسمية الجدول/العمود كإعادة تسمية موثوقة، كما يعتمد على القيود المسماة في عدد من الحالات.
3. https://alembic.sqlalchemy.org/en/latest/cookbook.html — يوضح خيارات baseline و`stamp`، والفصل بين schema/data migrations، وإمكانية تشغيل migrations عبر اتصال مشترك، مع أمثلة على `upgrade` و`downgrade`.

هذه الملاحظات مصدر توثيقي فقط؛ لا تحتوي بيانات اتصال أو أسرارًا.
