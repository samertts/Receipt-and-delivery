# Dialogs Inventory — Before

## Desktop Dialogs

### 1. LoginWindow (app.py:85)
| Field            | Widget      | Details               |
|------------------|-------------|-----------------------|
| Username         | QLineEdit   | No validation icon    |
| Password         | QLineEdit   | Echo mode: Password   |
| Submit           | QPushButton | "دخول"                |

### 2. ChangePasswordDialog (app.py:46)
| Field                | Widget      | Details               |
|----------------------|-------------|-----------------------|
| Current password     | QLineEdit   | Echo mode: Password   |
| New password         | QLineEdit   | Echo mode: Password   |
| Confirm password     | QLineEdit   | Echo mode: Password   |
| Save                 | QPushButton | "حفظ"                 |

### 3. ReceiptDialog (receipt_dialog.py:32)
| Field                | Widget      | Details               |
|----------------------|-------------|-----------------------|
| Transaction type     | QComboBox   | 4 types               |
| Sender org           | QComboBox   | 35 orgs               |
| Receiver org         | QComboBox   | 35 orgs               |
| Sender name          | QLineEdit   | Required              |
| Receiver name        | QLineEdit   | Required              |
| Sender job title     | QLineEdit   |                       |
| Receiver job title   | QLineEdit   |                       |
| Auth doc number      | QLineEdit   |                       |
| Auth date            | QDateEdit   | Calendar popup        |
| Status               | QComboBox   | Draft/Approved/etc    |
| Notes                | QLineEdit   |                       |
| Transport info       | QLineEdit   |                       |
| Additional comments  | QLineEdit   |                       |
| Items table          | QTableWidget| Dynamic rows          |
| Add sample button    | QPushButton | "+ إضافة عينة"        |
| Save                 | QPushButton | "حفظ"                 |
| Cancel               | QPushButton | "إلغاء"               |

### 4. ReceiptDetailDialog (receipt_detail_dialog.py:44)
| Component       | Widget      | Details               |
|-----------------|-------------|-----------------------|
| All fields      | QLabel      | Read-only labels      |
| Items table     | QTableWidget| Read-only             |
| Attachments table| QTableWidget| With open buttons    |
| Print PDF       | QPushButton | "طباعة PDF"           |
| Attach file     | QPushButton | "إرفاق ملف"           |
| Close           | QPushButton | "إغلاق"               |

### 5. OrgDialog (org_page.py:53)
| Field         | Widget      | Details               |
|---------------|-------------|-----------------------|
| Name          | QLineEdit   | Required              |
| Code          | QLineEdit   | Required              |
| Type          | QComboBox   | 7 types               |
| Governorate   | QComboBox   | 18 governorates       |
| Address       | QLineEdit   |                       |
| Phone         | QLineEdit   |                       |
| Email         | QLineEdit   |                       |
| Notes         | QLineEdit   |                       |
| Status        | QComboBox   | Active/Inactive/Archived |
| Save          | QPushButton | "حفظ"                 |
| Cancel        | QPushButton | "إلغاء"               |

## Common Dialogs
- QMessageBox: Used for confirmations and errors
- QFileDialog: Used for file selection (attachments, CSV export)
- QInputDialog: Used for password reset in UsersPage

## Web Modals

### Organizations.vue — Add Organization Modal
| Field    | Input Type  |
|----------|-------------|
| Name     | text        |
| Code     | text        |
| Governorate| text      |
| Phone    | text        |
| Email    | text        |
| Save     | button      |
| Cancel   | button      |

### Settings.vue — Add User Form
| Field    | Input Type  |
|----------|-------------|
| Username | text        |
| Full Name| text        |
| Password | password    |
| Role     | select      |
| Save     | button      |
