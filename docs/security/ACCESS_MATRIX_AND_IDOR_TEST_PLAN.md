# مصفوفة الوصول واختبارات API ضد IDOR

**المستودع:** `samertts/Receipt-and-delivery`
**الغرض:** تمثيل نطاق الوصول الحالي والمطلوب، وتحويل مخاطر IDOR إلى اختبارات آلية قابلة للتنفيذ.
**الحالة:** خطة اختبار أمنية مرتبطة بـTenant Isolation؛ لا تُعد إثباتًا بأن العزل المؤسسي مكتمل قبل إضافة `tenant_id` وفرضه في كل طبقات Backend.

## 1. المبدأ الأمني

> يجب أن يعتمد الوصول على **المستخدم المصادق عليه + الدور + tenant/facility context + ملكية المورد**، وليس على معرف المورد الذي يرسله العميل وحده.

الدور يحدد العملية المسموحة، بينما يحدد `tenant_id` و`facility_id` نطاق البيانات. لذلك فإن امتلاك المستخدم صلاحية `view_transactions` لا يعني امتلاكه حق رؤية معاملات كل المؤسسات.

## 2. Trust Boundaries

```mermaid
flowchart LR
    C[Browser / Desktop Client] -->|HTTPS + session/CSRF أو Bearer مؤقت| A[FastAPI Auth Dependencies]
    A -->|user_id + role + tenant context| P[Permission + Ownership Policy]
    P --> R[Scoped Repository / Service]
    R --> D[(PostgreSQL)]
    D -->|Defense in depth| Q[PostgreSQL RLS]
    R --> X[Export / Attachment / Sync]
    X -->|نفس tenant scope| D
    J[Background Job] -->|TenantContext صريح| R
    S[Audit Log] <--|لا PHI ولا tokens| P
```

يجب اعتبار كل سهم حدًا يحتاج اختبارًا. أكثر الأخطاء خطورة هي أن يتحقق API من الدور ثم يستعلم عن المورد بالـID فقط، أو أن يستخدم Job أو cache سياق Tenant سابقًا.

## 3. الأدوار والصلاحيات الحالية

المصفوفة التالية مستخرجة من `backend/app/core/rbac.py`. وهي تصف **RBAC الحالي**، وليست بديلًا عن ownership filtering الذي يجب إضافته مع Tenant Isolation.

| الدور | Dashboard | Transactions قراءة | إنشاء | تعديل | حذف | Reports | Users | Organizations | Audit logs | Sync | Devices |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `admin` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | إدارة | إدارة | ✓ | ✓ | ✓ |
| `supervisor` | ✓ | ✓ | ✓ | ✓ | — | ✓ | قراءة | إدارة | — | — | ✓ |
| `user` | ✓ | ✓ | ✓ | — | — | — | — | قراءة | — | — | ✓ |
| `auditor` | ✓ | ✓ | — | — | — | — | — | قراءة | ✓ | — | — |
| anonymous | — | — | — | — | — | — | — | — | — | — | — |

### ملاحظة مهمة على الوضع الحالي

هذا الجدول يبين صلاحيات العملية فقط. لا يوجد في Backend الحالي عزل مؤسسي كامل مستند إلى `tenant_id` في `User` والكيانات الحساسة. لذلك يجب قراءة خلايا الوصول إلى بيانات Tenant آخر على أنها **متطلب أمني مستهدف واختبار مانع للإصدار**، لا كضمان متاح تلقائيًا من RBAC الحالي.

## 4. مصفوفة النطاق المؤسسي

| Actor | مورد داخل Tenant نفسه | مورد في Facility مصرح | مورد في Tenant آخر | معرّف صحيح بلا ملكية |
|---|---|---|---|---|
| Operator | حسب role | حسب facility policy | رفض `403` أو `404` | رفض `403` أو `404` |
| Supervisor | حسب role | قراءة/تعديل حسب السياسة | رفض | رفض |
| Tenant admin | كل موارد tenant | كل منشآت tenant فقط | رفض | رفض |
| Central auditor | قراءة محدودة ومُسجلة | قراءة محدودة ومُسجلة | مسموح فقط بصلاحية صريحة وaudit | حسب السياسة |
| Revoked device | لا push ولا pull | لا push ولا pull | رفض | رفض |
| Anonymous | رفض | رفض | رفض | رفض |

يجب ألا يسمح `tenant_id` أو `facility_id` الموجود في JSON أو query parameter بتوسيع النطاق. يحدد الخادم السياق من session/claims وعضوية المستخدم وتسجيل الجهاز، ثم يطابق المدخلات مع ذلك السياق.

## 5. مصفوفة API الحالية واختبارات IDOR

النتيجة المتوقعة في الجدول هي النتيجة بعد تفعيل ownership enforcement. أي اختبار يفشل حاليًا بسبب غياب tenant context يجب أن يبقى مانعًا للإصدار، لا أن يُحوّل إلى `skip` دائم.

| ID | المسار | العملية | صلاحية RBAC | سيناريو IDOR | النتيجة المتوقعة | سلامة البيانات |
|---|---|---|---|---|---|---|
| IDOR-TX-01 | `/api/transactions/{id}` | `GET` | `view_transactions` | User B يطلب transaction من Tenant A بمعرّف صحيح | `403` أو `404` بلا marker A | لا response data |
| IDOR-TX-02 | `/api/transactions/{id}` | `PUT` | `edit_transaction` | Supervisor B يعدل transaction A | `403` أو `404` | القيم الأصلية تبقى |
| IDOR-TX-03 | `/api/transactions/{id}` | `DELETE` | `delete_transaction` | Admin B يحذف transaction A | `403` أو `404` | الصف يبقى |
| IDOR-TX-04 | `/api/transactions` | `GET` | `view_transactions` | User B يستعمل search/filters تخص A | `200` بقائمة B فقط | لا marker A |
| IDOR-TX-05 | `/api/transactions/{id}/custody` | `POST` | `edit_transaction` | إضافة custody event إلى transaction A من B | `403` أو `404` | لا event جديد |
| IDOR-ORG-01 | `/api/organizations/{id}` | `GET` | `view_organizations` | قراءة organization A من User B | `403` أو `404` حسب policy | لا بيانات A |
| IDOR-ORG-02 | `/api/organizations/{id}` | `PUT/DELETE` | `manage_organizations` | Supervisor B يغير organization A | `403` أو `404` | لا mutation |
| IDOR-USER-01 | `/api/users/{id}` | `GET` | `view_users` | Supervisor B يقرأ user A | رفض حسب tenant membership | لا بيانات شخصية |
| IDOR-USER-02 | `/api/users/{id}` | `PUT/DELETE` | `manage_users` | Admin B يدير user A | رفض | لا mutation |
| IDOR-REP-01 | `/api/reports/transactions.xlsx` | `GET` | `view_reports` | تقرير B يحتوي filter أو cache من A | نجاح لنطاق B فقط | لا marker A في XLSX |
| IDOR-REP-02 | `/api/reports/transactions.pdf` | `GET` | `view_reports` | تقرير B يتضمن سجلات A | نجاح لنطاق B فقط | لا marker A في PDF |
| IDOR-SYNC-01 | `/api/sync/pull` | `GET` | `sync_data` | B يرسل branch/cursor خاصًا بـA | رفض أو أحداث B فقط | لا event A |
| IDOR-SYNC-02 | `/api/sync/push` | `POST` | `sync_data` | جهاز B يرسل `tenant_id=A` | رفض | لا SyncLog A |
| IDOR-WS-01 | `/api/notifications` | WebSocket | auth + origin | B يشترك في channel A | رفض أو لا events A | لا notification A |
| IDOR-ATT-01 | attachment endpoint | `GET` | حسب المورد | B يطلب attachment ID من A | `403` أو `404` | لا bytes/path A |
| IDOR-JOB-01 | background export/sync | worker | job scope | إعادة تشغيل Job A ضمن context B | رفض/عزل | لا artifact cross-tenant |

## 6. اختبارات عدم إنشاء tenant مزور

| ID | المدخل المزور | السلوك المطلوب |
|---|---|---|
| IDOR-MASS-01 | JSON `tenant_id=B` أثناء login في A | تجاهل أو رفض؛ المورد الناتج tenant A فقط |
| IDOR-MASS-02 | JSON `facility_id` لفرع غير مصرح | رفض؛ لا يتم نقل الملكية |
| IDOR-MASS-03 | Header `X-Tenant-ID=B` | لا يغير سياق الخادم |
| IDOR-MASS-04 | query `?tenant_id=B` | يرفض أو يتجاهل دون توسيع النطاق |
| IDOR-MASS-05 | `created_by`, `owner_id`, `device_id` مزورة | يحددها الخادم ولا يثق بالعميل |

## 7. قالب pytest لاختبارات القراءة والتعديل والحذف

```python
import pytest


def assert_denied_without_marker(response, marker):
    assert response.status_code in {403, 404}
    assert marker not in response.text


def test_tenant_b_cannot_read_tenant_a_transaction(client, tenant_fixture):
    login_as(client, tenant_fixture.user_b)
    response = client.get(f"/api/transactions/{tenant_fixture.tx_a.id}")
    assert_denied_without_marker(response, "A-SECRET-001")


def test_tenant_b_cannot_update_tenant_a_transaction(client, db, tenant_fixture):
    login_as(client, tenant_fixture.supervisor_b)
    response = client.put(
        f"/api/transactions/{tenant_fixture.tx_a.id}",
        json={"notes": "B-MUST-NOT-WRITE"},
    )
    assert_denied_without_marker(response, "A-SECRET-001")
    db.refresh(tenant_fixture.tx_a)
    assert tenant_fixture.tx_a.notes != "B-MUST-NOT-WRITE"


def test_tenant_b_cannot_delete_tenant_a_transaction(client, db, tenant_fixture):
    login_as(client, tenant_fixture.admin_b)
    response = client.delete(f"/api/transactions/{tenant_fixture.tx_a.id}")
    assert response.status_code in {403, 404}
    assert db.get(Transaction, tenant_fixture.tx_a.id) is not None
```

يجب أن تكون `tenant_fixture` مكونة من Tenant A وTenant B ومستخدمين وأجهزة ومرفقات وعلامات نصية مختلفة. استخدم قاعدة اختبار مؤقتة وrollback بعد كل حالة.

## 8. اختبارات القائمة والبحث والتقارير

لا يكفي اختبار endpoint بالـID؛ فالتسريب قد يحدث في القوائم أو البحث أو dashboard أو التصدير.

```python
@pytest.mark.parametrize("path", [
    "/api/transactions",
    "/api/dashboard/summary",
    "/api/reports/summary",
    "/api/reports/transactions.xlsx",
    "/api/reports/transactions.pdf",
])
def test_tenant_b_never_receives_tenant_a_marker(client, tenant_fixture, path):
    login_as(client, tenant_fixture.user_b)
    response = client.get(path)
    assert response.status_code < 500
    assert "A-SECRET-001" not in response.text
```

بالنسبة للملفات الثنائية، يجب فحص محتوى XLSX/PDF بعد فكّه أو استخراج النص، وليس `response.text` فقط. كما يجب تنفيذ request من A ثم B بنفس URL للتأكد من عدم إعادة cache خاص بـA.

## 9. اختبارات المزامنة والأجهزة

| الحالة | الإجراء | التوقع |
|---|---|---|
| جهاز B يرسل `tenant_id=A` | `POST /api/sync/push` | رفض وعدم إنشاء `SyncLog` |
| cursor من A مع session B | `GET /api/sync/pull` | أحداث B فقط أو رفض |
| branch A مع branch B | pull بــ`branch_id=A` | رفض/لا أحداث A |
| device revoked | push وpull بعد revoke | رفض فوري |
| duplicate key نفسه | push مرتين | نتيجة idempotent واحدة |
| نفس key بpayload مختلف | push conflict | quarantine بلا overwrite |
| Job A ثم Job B بالتوازي | تشغيل workerين | لا اختلاط في النتائج |

يجب كذلك التأكد من أن `tenant_id` المقرر في الخادم لا يأتي من payload وحده، وأن cursor وidempotency keys لا يعيدان بيانات من نطاق آخر.

## 10. PostgreSQL RLS Integration Tests

بعد إضافة ownership columns، شغّل هذه الاختبارات على PostgreSQL حقيقي داخل CI:

1. `SET LOCAL app.tenant_id = 'A'` يرى A فقط.
2. `SET LOCAL app.tenant_id = 'B'` يرى B فقط.
3. غياب tenant setting يفشل مغلقًا أو يعيد صفر صفوف.
4. تغيير tenant setting من application input لا يمنح صلاحية إضافية.
5. connection pool لا يترك setting من request سابق.
6. application role لا يملك `BYPASSRLS`.
7. direct SQL update خارج tenant لا يغير الصف.

لا تعتبر SQLite بديلًا عن اختبارات RLS؛ يمكن استخدامها لاختبارات repository، لكن RLS سلوك PostgreSQL خاص.

## 11. اختبارات التسريب غير المباشر

ابحث عن marker Tenant A في:

| السطح | الاختبار |
|---|---|
| response body | marker لا يظهر في JSON/HTML/error |
| headers | لا يظهر tenant أو resource حساس في header غير مقصود |
| logs | لا marker ولا token ولا PHI |
| audit | يسجل actor/scope دون payload حساس |
| WebSocket | لا events من A في channel B |
| cache | لا cache hit من A عند B |
| attachments | لا filename/path/bytes من A |
| exports | لا marker A في XLSX/PDF/CSV |
| support bundle | لا بيانات Tenant آخر |

## 12. قواعد منع الاختبارات الوهمية

لا تستخدم `skip` أو `xfail` لاختبارات IDOR دون issue وتاريخ انتهاء. لا تعتمد على status code فقط؛ افحص أيضًا أن قاعدة البيانات لم تتغير وأن marker لم يظهر. لا تستخدم مستخدم `admin` واحدًا لاختبار كل شيء، لأن ذلك يخفي أخطاء النطاق. ولا تختبر tenant isolation ببيانات متطابقة؛ يجب أن يكون لكل tenant marker مختلف.

## 13. معايير قبول الإصدار

لا يُسمح بترقية Tenant Isolation إلى production حتى تنجح جميع الاختبارات التالية على الأقل:

- القراءة والتعديل والحذف cross-tenant لكل resource حساس.
- القوائم والبحث وdashboard والتقارير دون cross-tenant marker.
- attachments وWebSocket وsync وbackground jobs ضمن النطاق نفسه.
- mass-assignment وforged tenant/facility/device fields مرفوضة.
- PostgreSQL RLS وconnection pool tests ناجحة.
- لا marker في logs أو exports أو support artifacts.
- rollback وrestore وmigration من قاعدة قديمة ناجحة.
- مراجعة يدوية للاستعلامات الحرجة وغياب `get_all()` غير المقيد.

## 14. مراجع

[1]: https://owasp.org/www-project-application-security-verification-standard/ "OWASP Application Security Verification Standard"
[2]: https://owasp.org/www-community/attacks/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet "OWASP IDOR Prevention Cheat Sheet"
[3]: https://www.postgresql.org/docs/current/ddl-rowsecurity.html "PostgreSQL Row Security Policies"
