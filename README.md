# نظام إدارة الاستلام المختبري

**Iraqi Laboratory Receipt & Delivery Management System**

تطبيق متكامل لإدارة استلام وتسليم العينات والمواد المختبرية، مع دعم واجهة سطح المكتب (PySide6) وواجهة ويب (FastAPI + Vue 3).

---

## المميزات

- **إيصالات استلام وتسليم** مع ترقيم تلقائي `LAB-YYYY-XXXXXX`
- **التحقق الإلزامي لمعادلة العينات** قبل الحفظ
- **إدارة المستخدمين والصلاحيات** (Admin / Supervisor / User / Auditor)
- **إدارة المؤسسات** الديناميكية
- **أنواع معاملات وأنواع عينات** ديناميكية
- **PDF احترافي** مع QR Code و Barcode وتوقيعات
- **سجل تدقيق (Audit Log)** غير قابل للتعديل
- **إدارة المرفقات** مع SHA-256 hash وضغط صور
- **نسخ احتياطي محلي**
- **واجهة سطح مكتب** (PySide6 + SQLite)
- **واجهة ويب** (FastAPI + Vue 3 + PostgreSQL)
- **ـPWA** (Progressive Web App) مع دعم عدم الاتصال
- **ـAPI RESTful** مع توثيق Swagger
- **ـDocker** support
- **ـCI/CD** via GitHub Actions

---

## هيكل المشروع

```
├── backend/                    # FastAPI web API
│   ├── app/
│   │   ├── api/v1/            # API endpoints
│   │   ├── core/              # Config, security, logging, exceptions
│   │   ├── db/                # Database session & base
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   └── tests/                 # API tests
├── frontend/                   # Vue 3 PWA
│   └── src/
│       ├── api/               # API client
│       ├── components/        # Layout & shared components
│       ├── pages/             # Page components
│       ├── router/            # Vue Router
│       └── stores/            # Pinia stores
├── lab_system/                 # PySide6 desktop app
│   └── app/
│       ├── auth/              # Authentication & permissions
│       ├── database/          # SQLite schema & migrations
│       ├── printing/          # PDF generation
│       ├── services/          # Business logic
│       └── ui/                # Desktop UI
├── scripts/                    # Utility scripts
├── installer/                  # Windows installer (Inno Setup)
├── tests/                     # Desktop app tests
├── docker-compose.yml         # Docker setup
└── .env.example               # Environment template
```

---

## التشغيل السريع

### واجهة سطح المكتب

```bash
pip install -r requirements.txt
python main.py
```

### واجهة الويب (API)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

الوثائق التفاعلية: http://localhost:8000/api/docs

### باستخدام Docker

```bash
cp .env.example .env
docker compose up -d
```

### بيانات الدخول الافتراضية

| المستخدم | كلمة المرور | الصلاحية |
|---------|------------|---------|
| admin | Admin@123 | Admin |

⚠️ **يجب تغيير كلمة المرور الافتراضية فور تسجيل الدخول الأول.**

---

## التوثيق

| الملف | الوصف |
|------|-------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | شرح العمارة التقنية |
| [SECURITY.md](SECURITY.md) | السياسات الأمنية |
| [API.md](API.md) | توثيق API |
| [CONTRIBUTING.md](CONTRIBUTING.md) | دليل المساهمة |
| [CHANGELOG.md](CHANGELOG.md) | سجل التغييرات |

---

## الترخيص

هذا النظام مملوك لـ Iraqi Health Laboratory Directorate.
