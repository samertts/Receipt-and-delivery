# API Documentation - نظام إدارة الاستلام المختبري

Base URL: `/api`

Interactive docs: `/api/docs` (Swagger) | `/api/redoc` (ReDoc)

---

## Authentication

### GET /api/auth/me

يعيد بيانات المستخدم الحالي، الدور، الصلاحيات الفعلية، وجميع الأدوار المدعومة. يتطلب access token صالحًا.

### POST /api/auth/refresh

Authenticate user and receive JWT token.

**Request:**
```json
{
  "username": "admin",
  "password": "Admin@123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

## Localization

تدعم الواجهة العربية والإنجليزية. يُحفظ اختيار المستخدم محليًا، وتتحول الصفحة تلقائيًا بين اتجاهي `RTL` و`LTR`. تُرسل صفحة التقارير معامل `lang=ar` أو `lang=en` إلى Backend لتوطين عناوين وحقول ملفات PDF وExcel.

## Dashboard

### GET /api/dashboard/summary

إرجاع مؤشرات لوحة التحكم وبيانات الرسوم البيانية للمستخدمين المصرح لهم برؤية لوحة التحكم.

**Query Parameters:**

| Param | Type | Description |
|---|---|---|
| days | int | عدد أيام الاتجاه اليومي، من 7 إلى 90، والقيمة الافتراضية 7 |

**Response data:**

```json
{
  "summary": {
    "total_transactions": 125,
    "total_organizations": 18,
    "by_status": {
      "approved": 80,
      "draft": 20,
      "rejected": 10,
      "archived": 10,
      "cancelled": 5
    }
  },
  "trends": {
    "total": 12,
    "approved": 8,
    "draft": -4,
    "orgs": 3
  },
  "trend": [{"date": "2026-08-24", "count": 16}],
  "by_type": [{"key": "استلام", "count": 70}],
  "recent_transactions": []
}
```

تُرجع الواجهة الخلفية هذه البيانات داخل غلاف الاستجابة القياسي `{success, message, data, meta}`. يتطلب endpoint صلاحية `view_dashboard`.

---

## Reports

### GET /api/reports/summary

يعيد تقرير المعاملات والإحصائيات وفق الفلاتر. يدعم `start_date` و`end_date` و`status` و`transaction_type`، إضافة إلى معامل `lang` الاختياري بقيمة `ar` أو `en`.

### GET /api/reports/transactions.xlsx

ينزّل تقرير المعاملات والإحصائيات بصيغة Excel باللغة المختارة.

### GET /api/reports/transactions.pdf

ينزّل تقرير المعاملات والإحصائيات بصيغة PDF باللغة المختارة.

يتطلب الملخص والتصدير صلاحية `view_reports`.

---

## Real-time Notifications

### WebSocket /api/ws/notifications

يفتح المستخدم المصادق عليه اتصال WebSocket لاستقبال تغيّرات المعاملات فور حدوثها. بسبب قيود متصفح WebSocket، يُمرَّر access token في query parameter أثناء المصافحة:

```text
ws://localhost:8000/api/ws/notifications?token=<access-token>
```

في الإنتاج يُستخدم `wss://` تلقائيًا عبر نفس مضيف الواجهة. يرسل الخادم رسالة `connected` بعد نجاح الاتصال، ويدعم رسالة `ping` من العميل ويرد عليها بـ `pong` للحفاظ على الاتصال.

**رسالة تغيير معاملة:**

```json
{
  "id": "notification-uuid",
  "type": "transaction",
  "event": "created|updated|status_changed|deleted",
  "title": "تم تحديث معاملة",
  "message": "TXN-... — الحالة: approved",
  "transaction_id": "uuid",
  "transaction_no": "TXN-...",
  "status": "approved",
  "actor_username": "admin",
  "created_at": "2026-08-24T20:00:00+00:00"
}
```

يتم رفض الرموز المنتهية أو المبطلَة والحسابات غير النشطة برمز إغلاق WebSocket `1008`. التشغيل الافتراضي يستخدم عامل Backend واحدًا للحفاظ على مشاركة اتصالات WebSocket داخل العملية؛ عند استخدام عدة عمال أو عدة نسخ يجب إضافة broker مركزي مثل Redis للبث بين العمليات.

---

## RBAC

يطبق Backend الصلاحيات على كل endpoint، كما تمنع الواجهة فتح المسارات غير المسموح بها وتخفي روابط Sidebar التي لا يملك المستخدم صلاحيتها. الأدوار المدعومة هي `admin` و`supervisor` و`user` و`auditor`.

| الصلاحية | الأدوار المسموح لها |
|---|---|
| `view_dashboard` | admin, supervisor, user, auditor |
| `view_transactions` | admin, supervisor, user, auditor |
| `create_transaction` | admin, supervisor, user |
| `edit_transaction` | admin, supervisor |
| `delete_transaction` | admin |
| `view_reports` | admin, supervisor |
| `view_users` | admin, supervisor |
| `manage_users` | admin |
| `view_audit_logs` | admin, auditor |
| `manage_organizations` | admin, supervisor |
| `manage_settings` | admin |
| `use_devices` | admin, supervisor, user |

### User management

يدعم `GET /api/users` معاملات `role` و`status=active|inactive` للتصفية. يدعم `PUT /api/users/{id}` تعديل `full_name` و`role` و`password` و`status`. لا يمكن تعطيل المستخدم الحالي أو إزالة آخر مدير نظام نشط.

---

## Device integrations

لا تضيف تكاملات الأجهزة الحالية endpoints جديدة إلى Backend؛ تتم الكاميرا والباركود وOCR وNFC والطباعة من المتصفح بعد إذن المستخدم عبر `/devices`. يدعم قارئ USB الذي يعمل كلوحة مفاتيح إرسال الرمز ثم `Enter`، وتبقى نتيجة OCR نصًا قابلًا للتحرير ولا تُحفظ تلقائيًا.

يتطلب مسار الواجهة صلاحية `use_devices`. تحتاج الكاميرا إلى سياق آمن (`HTTPS` أو `localhost`)، بينما Web NFC اختياري وغير متاح في أغلب بيئات سطح المكتب وiOS. تستخدم الطباعة `window.print()` للطابعات المسجلة في نظام التشغيل. التحكم الخام بالطابعات الحرارية أو USB/Serial غير متاح مباشرة للمتصفح، ويجب تنفيذه لاحقًا عبر جسر محلي موثوق يستمع إلى `127.0.0.1` ويصادق كل طلب.

لخطوات الإعداد والتوافق والأمان راجع [DEVICE_INTEGRATION.md](DEVICE_INTEGRATION.md).

---

## Transactions

### GET /api/transactions

List transactions (requires auth).

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| page | int | Page number (default: 1) |
| limit | int | Items per page (default: 20, max: 100) |
| status | string | Filter by status: draft/approved/rejected/archived/cancelled |
| search | string | Search in transaction number |

### POST /api/transactions

Create a new transaction.

**Request:**
```json
{
  "transaction_type": "Sample Receipt",
  "sender_organization_id": "uuid",
  "receiver_organization_id": "uuid",
  "sender_name": "مختبر بغداد",
  "receiver_name": "مختبر الكرخ",
  "authorization_no": "AUTH-001",
  "transaction_date": "2026-05-27",
  "items": [
    {
      "sample_type": "Serum",
      "total_count": 10,
      "valid_count": 8,
      "damaged_count": 1,
      "rejected_count": 1,
      "nonconforming_count": 0,
      "transport_condition": "Cooler box"
    }
  ]
}
```

### GET /api/transactions/{id}

Get transaction details.

### PUT /api/transactions/{id}

Update transaction.

### DELETE /api/transactions/{id}

Delete transaction (admin only).

---

## Users

### GET /api/users

List users (admin/supervisor).

### POST /api/users

Create user (admin only).

**Request:**
```json
{
  "username": "newuser",
  "full_name": "New User",
  "password": "Strong@Pass123",
  "role": "user"
}
```

### PUT /api/users/{id}

Update user.

### DELETE /api/users/{id}

Delete user.

---

## Organizations

### GET /api/organizations

List organizations.

### POST /api/organizations

Create organization (admin/supervisor).

### GET /api/organizations/{id}

Get organization details.

### PUT /api/organizations/{id}

Update organization.

### DELETE /api/organizations/{id}

Delete organization.

---

## Audit Logs

### GET /api/audit-logs

List audit logs (admin/auditor only).

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| action_type | string | Filter by action type |

---

## Health

### GET /api/health

Health check endpoint (no auth required).

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "app_name": "نظام إدارة المعاملات المختبرية"
}
```
