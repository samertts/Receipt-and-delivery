# Page Inventory — Before

## Desktop App Pages

| # | Page Class        | File                        | Purpose                     | Has Search | Has Filters | Has Table | Has Pagination | Has Actions |
|---|-------------------|-----------------------------|-----------------------------|------------|-------------|-----------|----------------|-------------|
| 1 | DashboardPage     | lab_system/app/ui/app.py    | Welcome + system health     | No         | No          | No        | No             | No          |
| 2 | ReceiptsPage      | ui/receipts_page.py         | Receipt management          | Yes        | Yes (3)     | Yes       | Yes            | Per row     |
| 3 | OrgPage           | ui/org_page.py              | Organization management     | Yes        | No          | Yes       | No             | Per row     |
| 4 | UsersPage         | ui/users_page.py            | User management + creation  | No         | No          | Yes       | No             | Per row     |
| 5 | ReportsPage       | ui/reports_page.py          | Reports & statistics        | No         | Yes (date)  | Yes       | No             | Export      |
| 6 | SettingsPage      | ui/settings_page.py         | System settings             | No         | No          | No        | No             | Save        |
| 7 | AuditPage         | ui/audit_page.py            | Audit log viewer            | No         | No          | Yes       | No             | No          |
| 8 | BackupPage        | ui/backup_page.py           | Backup & restore management | No         | No          | Yes       | No             | Per row     |

## Web Frontend Pages

| # | Component            | Route                | Purpose                  | Has Search | Has Filters | Has Table |
|---|----------------------|----------------------|--------------------------|------------|-------------|-----------|
| 1 | Dashboard.vue        | /dashboard            | Statistics + activity    | No         | No          | Yes       |
| 2 | TransactionsList.vue | /transactionslist     | Transaction list         | Yes        | Yes (1)     | Yes       |
| 3 | TransactionDetails.vue| /transactiondetails  | View transaction         | No         | No          | Yes       |
| 4 | NewTransaction.vue   | /newtransaction       | Create transaction       | No         | No          | No        |
| 5 | Organizations.vue    | /organizations        | Organization list        | No         | No          | Yes       |
| 6 | Reports.vue          | /reports              | Reports                  | No         | No          | Yes       |
| 7 | Settings.vue         | /settings             | User management          | No         | No          | Yes       |
| 8 | AuditLogs.vue        | /auditlogs            | Audit log viewer         | Yes        | Yes (1)     | Yes       |
| 9 | Login.vue            | /                     | Authentication           | No         | No          | No        |

## Desktop Dialogs

| Dialog Class              | File                        | Purpose                  | Type         |
|---------------------------|-----------------------------|--------------------------|--------------|
| LoginWindow(QDialog)      | app.py                      | Authentication           | Modal        |
| ChangePasswordDialog(QDialog) | app.py                  | Password change          | Modal        |
| ReceiptDialog(QDialog)    | ui/receipt_dialog.py        | Create/Edit receipt      | Modal        |
| ReceiptDetailDialog(QDialog)| ui/receipt_detail_dialog.py| View receipt details    | Modal        |
| OrgDialog(QDialog)        | ui/org_page.py              | Create/Edit organization | Modal        |

## Web Frontend Dialogs/Modals

| Component  | Location                | Purpose                  | Type         |
|------------|-------------------------|--------------------------|--------------|
| Organizations.vue | Inline modal      | Add new organization     | Modal (v-if) |
| Settings.vue      | Details/summary    | Add new user             | Inline       |
