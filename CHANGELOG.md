# Changelog - نظام إدارة الاستلام المختبري

جميع التغييرات المهمة على المشروع سيتم توثيقها في هذا الملف.

يعتمد هذا المشروع على مبادئ Semantic Versioning.

---

# [Unreleased]

## Added

* إضافة قسم Smart Insights في Dashboard يولد توصيات تشغيلية محلية من المسودات والمعاملات المرفوضة واتجاه حجم العمل دون إرسال بيانات المعاملات إلى خدمة خارجية.
* إضافة تخطيط متجاوب لنموذج المعاملة مع قوائم اقتراحات قابلة للتمرير وتنظيف مستمعات النقر عند مغادرة الصفحة.

## Fixed

* إصلاح تداخل الحقول واختفاء التمرير في الواجهة الأمامية عبر حاوية تمرير رئيسية وقواعد `min-width` و`overflow` موحدة.
* إضافة أشرطة تمرير عمودية وأفقية لحوارات المعاملات وتفاصيل الإيصال والمؤسسات في تطبيق PySide6، مع إبقاء أزرار الإجراء ظاهرة.

* إضافة نظام RBAC مركزي بالأدوار `admin` و`supervisor` و`user` و`auditor` مع claims الصلاحيات داخل access token وendpoint `/api/auth/me`.
* إضافة حارس مسارات في الواجهة وصفحة Access Denied وإخفاء روابط Sidebar غير المسموح بها.
* توسيع إدارة المستخدمين لتصفية الحسابات وتعديل الدور والحالة وتفعيل أو تعطيل المستخدمين مع حماية آخر مدير نشط.
* إضافة مركز أجهزة محمي بصلاحية `use_devices` يدمج كاميرا/باركود ZXing، قارئات USB بنمط لوحة المفاتيح، OCR عربي/إنجليزي داخل المتصفح، Web NFC عند الدعم، والطباعة الأصلية عبر المتصفح.
* إضافة فحص حالة الجسر المحلي الاختياري دون فتح تحكم غير موثّق بالأجهزة، مع توثيق التوافق والخصوصية وخطوات التشغيل في `DEVICE_INTEGRATION.md`.
* تجهيز سكربت `scripts/build_windows.ps1` لبناء EXE محمول ومثبت Inno Setup وتوليد SHA-256، مع إصلاح مسارات الموارد و`VERSION` عند التشغيل عبر PyInstaller.
* إصلاح ترتيب Windows CI ليتحقق من مدخلات المثبت بعد إنشاء EXE، وتمرير رقم الإصدار تلقائيًا إلى Inno Setup.
* تحسين قياس وقت بدء التشغيل والذاكرة ليعمل على Windows وLinux وmacOS، مع استخدام Windows API عند غياب وحدة `resource`.
* جعل اختبارات قياس الذاكرة وCPU واختبارات SQLite WAL معزولة ومتوافقة مع Windows، بما يرفع موثوقية بوابة بناء EXE.
* إضافة `psutil` لقياس ذاكرة تطبيق سطح المكتب على Windows، وتكييف benchmark إنشاء schema مع اختلاف زمن I/O بين الأنظمة.
* إضافة Auto-updater آمن لتطبيق Windows: manifest عبر HTTPS موقّع بـ Ed25519، تحقق SHA-256، تنزيل مؤقت، تشغيل Inno Setup دون `shell=True`، وواجهة فحص تحديثات داخل تطبيق PySide6.
* ربط Windows CI بتجهيز public key وتوليد `update.json` عند الإصدارات الموسومة، مع اختبارات تحقق للتوقيع والحجم والتنظيف عند فشل التنزيل.
* إضافة فحص تحديثات تلقائي مؤجل بعد 3 ثوانٍ من بدء تشغيل Windows في خيط خلفي، بصمت عند عدم وجود تحديث أو فشل الاتصال، مع إبقاء التثبيت بموافقة المستخدم.

* دعم العربية والإنجليزية في الواجهة مع حفظ اختيار اللغة وتحديث اتجاه الصفحة تلقائيًا بين RTL وLTR.
* توطين صفحة Reports وملفات PDF وExcel مع تمرير معامل `lang` إلى Backend.

* إضافة قناة WebSocket `/api/ws/notifications` للتنبيهات الفورية عند إنشاء أو تحديث أو حذف المعاملات وتغيّر حالة الحيازة.
* إضافة مركز إشعارات في الواجهة مع عدّاد غير المقروء، القراءة الفردية والجماعية، حالة الاتصال، وإعادة الاتصال التلقائية.
* إضافة endpoint `/api/dashboard/summary` لإرجاع مؤشرات المعاملات وتوزيع الحالات والاتجاه اليومي وأنواع المعاملات وآخر المعاملات.
* إضافة رسوم بيانية تفاعلية ومتجاوبة في Dashboard للاتجاه اليومي وتوزيع أنواع المعاملات.
* اختبارات تكامل Vue وAxios وPinia تغطي غلاف API، تجديد الرموز، المصادقة، عمليات المعاملات CRUD، وواجهة تسجيل الدخول.
* تشغيل اختبارات الواجهة مع التغطية عبر `npm run test:unit` وربطها بخط GitHub Actions.
* وظيفة CI مستقلة لاختبارات Backend وRuff لمنع عودة أعطال عقود API.
* إضافة اختبارات WebSocket في Backend واختبارات Notification store في الواجهة.

## Fixed

* ربط أحداث المعاملات بالبث بعد نجاح commit فقط، لمنع إرسال تنبيهات عن عمليات فاشلة.
* إصلاح WebSocket لاستخدام جلسة قاعدة البيانات المحقونة بدل اتصال إنتاج مباشر أثناء الاختبارات.
* إصلاح Dashboard ليعتمد على بيانات إحصائية موحدة من Backend بدل طلبات متعددة وقيم تقديرية.
* إزالة النسبة العشوائية الخاصة باتجاه المؤسسات واستبدالها بنسبة محسوبة من بيانات الفترات الزمنية.
* توحيد إصدارات Pillow وpytest بين المتطلبات الجذرية والخلفية لمنع فشل تثبيت البيئة.
* إصلاح استيرادات مفقودة في إعدادات الخلفية، التطبيق الرئيسي، تبعيات المصادقة، وراوتر المصادقة.
* منع محدد معدل الطلبات من تلويث اختبارات API المتسلسلة، مع إبقاء إمكانية فرضه عبر `RATE_LIMIT_FORCE_ENABLED`.
* إصلاح عدم توافق واجهة Vue مع غلاف استجابة API الموحد، بما في ذلك تسجيل الدخول وتجديد الرموز وبيانات القوائم.
* إصلاح حساب إجمالي المعاملات في الواجهة ليستعمل `meta.total` من Backend بدل الاعتماد على طول الصفحة الحالية.
* إصلاح عرض رسالة خطأ تسجيل الدخول ورسائل متجر المعاملات من صيغة Backend الموحدة.
* تحديث فحوص الصحة في Backend لاستخدام وقت UTC واعٍ بالمنطقة الزمنية.
* توحيد رسائل أخطاء API في الواجهة مع دعم `message` و`detail` و`meta.error_code`.

## Improved

* إضافة فك مركزي لغلاف الاستجابة في عميل Axios مع الاحتفاظ بـ `response.envelope` و`response.meta` للتصفح والرسائل.
* جعل معترض تجديد الرمز أكثر متانة عند غياب إعدادات الطلب الأصلية.
* تحسين توقيع تغيير كلمة المرور باستخدام رمز اختياري بدل قيمة نصية فارغة.

---

# [1.2.0-rc1] - 2026-06-17

الحالة: Release Candidate

## Added

* Centralized dependency injection container (ServiceContainer)
* Service layer for all backend API routes
* DashboardService, DesktopAuditService, DesktopSettingsService, BackupListingService
* Health endpoints: /health, /health/live, /health/ready, /health/version, /health/dependencies
* Last-admin protection (cannot delete last admin)
* Self-role-change protection (admin cannot change own role)
* Fail-closed permission decorator (raises error when user=None)

## Changed

* All API routes now use service layer (AuthService, UserService, OrganizationService, TransactionService, AuditService, SyncService)
* Error response format standardized: error_code and status_code moved to meta block
* Response envelope middleware cleaned up (removed duplicate)
* Desktop UI pages (dashboard, audit, settings, backup) now use service layer

## Fixed

* Cross-layer violations in desktop UI (12 violations eliminated)
* UI call sites bypassing authorization (receipts_page.py, receipt_dialog.py)
* Test fixture ordering issues (conftest.py rewritten for robustness)
* Ruff lint errors (unused imports)

## Security

* Fail-closed @with_permission decorator
* Last-admin protection
* Self-role-change protection
* All endpoints verified with RBAC

---

# [1.2.0-dev] - Development Branch

الحالة: Development Only

الفرع:

feature/v1.2.0-dev

لم يتم دمج هذه التغييرات في الإنتاج.

## Added

* Refresh Token Rotation with Blacklist
* Logout Endpoint with Token Blacklisting
* Change Password Endpoint
* Redis-backed Rate Limiter with In-Memory Fallback
* Transaction Deep Update (Add/Delete Items via PUT)
* Pagination using X-Total-Count
* Organization Search Dropdowns
* Sample Type Autocomplete
* Audit Changes JSON Viewer
* Dashboard Accurate Counters
* Network Connectivity Diagnostics
* Real HTTP Transport in APIClient

## Changed

* Block inactive users from login and protected endpoints
* Rename RateLimiter to MemoryRateLimiter
* Remove unused ROLE_HIERARCHY
* Restrict transaction deletion to administrators

## Notes

This branch is under development and is not part of the production release.

---

# [1.1.0] - 2026-06-08

الحالة: Production Release

Tag:

v1.1.0

## Fixed

### Full-Text Search (FTS)

* Fixed SQLite content-sync FTS compatibility issues
* Fixed hyphen handling in search queries
* Fixed hard delete cleanup for FTS records
* Preserved FTS entries during soft delete
* Rebuilt FTS entries correctly during restore operations

### Backup & Recovery

* Replaced file-copy backups with sqlite3.Connection.backup()
* Added WAL checkpoint handling
* Improved backup consistency during active database usage
* Fixed unclosed recovery connections
* Protected recovery procedures against WAL-related failures

### Attachments

* Added SHA-256 duplicate detection
* Prevented duplicate file storage

### Diagnostics

* Expanded startup diagnostics to validate all production indexes

### Security

* Block inactive users at login
* Block inactive users on protected endpoints
* Fixed ForbiddenError instantiation issue
* Removed unused ROLE_HIERARCHY references

### CI/CD

* Fixed Inno Setup installer path
* Improved release version synchronization

### Testing

* Fixed SQLAlchemy model registration during tests

## Changed

* VERSION file is now the single source of truth
* Application version automatically reads from VERSION
* All version references synchronized to 1.1.0

## Production Certification

* Tests: 26/26 PASS
* Build Certification: 117/117 PASS
* Migration Certification: 328/328 PASS
* FTS Integrity: PASS
* Backup Integrity: PASS
* Recovery Integrity: PASS
* Attachment Integrity: PASS
* Version Governance: PASS
* CI/CD Validation: PASS

---

# [1.0.0] - 2026-05-27

الحالة: Initial Production Baseline

## Added

### Desktop Application

* PySide6 Desktop Application
* SQLite Local Database
* Full Offline Operation

### Web Platform

* FastAPI Backend
* PostgreSQL Support
* Vue 3 Progressive Web Application (PWA)

### Core Features

* Role-Based Access Control (RBAC)
* REST API
* Swagger / ReDoc Documentation
* Structured Logging
* Centralized Error Handling
* Audit Logging
* Dynamic Receipt Numbering
* PDF Generation
* QR Code Support
* Barcode Support
* Attachment Management
* Migration Framework
* Backup Framework
* Iraqi Health Organization Seed Data
* Docker Deployment Support
* GitHub Actions CI/CD
* Arabic RTL Support

### Security

* bcrypt Password Hashing
* JWT Authentication
* CORS Protection
* Input Validation
* SQL Injection Protection
* Migration Locking
* Immutable Audit Logs

## Notes

* Default Credentials: admin / Admin@123
* Desktop Application Works Fully Offline
* Web Platform Requires PostgreSQL
* This version represents the initial production baseline

---

# Version Policy

Production Branch:
main

Production Release:
v1.1.0

Development Branch:
feature/v1.2.0-dev

Rules:

* No direct development on main
* No direct commits to production releases
* All new features start from feature branches
* All merges require review and validation
* Production releases must be tagged before deployment

---

Last Production Release:

v1.1.0

Repository:

[git@github.com](mailto:git@github.com):samertts/Receipt-and-delivery.git
