# API Documentation - نظام إدارة الاستلام المختبري

Base URL: `/api`

Interactive docs: `/api/docs` (Swagger) | `/api/redoc` (ReDoc)

---

## Authentication

### POST /api/auth/login

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
