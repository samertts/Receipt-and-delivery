# Navigation Map — Before

## Desktop App (PySide6)

### Layout
```
┌──────────────────────┬──────────────────────────────────────┐
│   Sidebar            │   Content Area                       │
│   QListWidget        │   QStackedWidget                     │
│   240px fixed        │                                      │
│                      │                                      │
│   لوحة التحكم         │   DashboardPage                     │
│   الإيصالات           │   ReceiptsPage                      │
│   الجهات والمؤسسات    │   OrgPage                           │
│   المستخدمون والصلاحيات│   UsersPage                         │
│   التقارير            │   ReportsPage                       │
│   الإعدادات           │   SettingsPage                      │
│   سجل التدقيق         │   AuditPage                         │
│   النسخ الاحتياطي     │   BackupPage                        │
└──────────────────────┴──────────────────────────────────────┘
```

### Navigation Items
| Key       | Label               | Permission Required | Page Class      |
|-----------|---------------------|-------------------|-----------------|
| dashboard | لوحة التحكم          | dashboard.view    | DashboardPage   |
| receipts  | الإيصالات            | receipts.read     | ReceiptsPage    |
| orgs      | الجهات والمؤسسات     | organizations.read| OrgPage         |
| users     | المستخدمون والصلاحيات | users.read       | UsersPage       |
| reports   | التقارير             | reports.read     | ReportsPage     |
| settings  | الإعدادات            | settings.read    | SettingsPage    |
| audit     | سجل التدقيق          | audit.read       | AuditPage       |
| backup    | النسخ الاحتياطي      | backup.create    | BackupPage      |

- Items filtered by permission
- No sub-navigation, no breadcrumbs, no tabs
- No active indicator styling
- No hover effects
- No icons

## Web Frontend (Vue 3)

### Layout
```
┌─────────────────────────────────────────────────────────────┐
│  [Logo] [Dashboard] [Transactions] [New] ... [User] [Logout]│
├─────────────────────────────────────────────────────────────┤
│                      <router-view />                        │
│                       (Page content)                        │
└─────────────────────────────────────────────────────────────┘
```

### Navigation Items
| Route               | Label       |
|---------------------|-------------|
| /dashboard          | لوحة التحكم  |
| /transactionslist   | المعاملات    |
| /newtransaction     | معاملة جديدة |
| /organizations      | المؤسسات     |
| /reports            | التقارير     |
| /settings           | الإعدادات    |
| /auditlogs          | سجل التدقيق  |

- Horizontal top navbar
- Active state: `bg-blue-50 text-blue-700`
- No sidebar
- No grouping
