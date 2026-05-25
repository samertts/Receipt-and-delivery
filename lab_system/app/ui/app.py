from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QMainWindow, QMessageBox, QPushButton, QStackedWidget, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget
)

from lab_system.app.audit.logger import log_action
from lab_system.app.database.db import init_db
from lab_system.app.services.auth_service import AuthService
from lab_system.app.services.seed_service import seed_organizations
from lab_system.app.services.user_service import seed_default_users
from lab_system.app.services.catalog_service import seed_defaults, list_transaction_types, list_sample_types
from lab_system.app.services.org_service import list_organizations
from lab_system.app.services.receipt_service import (
    create_receipt, search_receipts, update_receipt, get_receipt_details, archive_receipt, soft_delete_receipt
)
from lab_system.app.utils.constants import APP_NAME, DEFAULT_WINDOW_SIZE, THEME


class LoginWindow(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.user = None
        self.auth = AuthService()
        self.setWindowTitle('تسجيل الدخول')
        self.setLayoutDirection(Qt.RightToLeft)
        self.setFixedWidth(420)
        layout = QVBoxLayout(self)
        self.username = QLineEdit()
        self.username.setPlaceholderText('اسم المستخدم')
        self.password = QLineEdit()
        self.password.setPlaceholderText('كلمة المرور')
        self.password.setEchoMode(QLineEdit.Password)
        submit = QPushButton('دخول')
        submit.clicked.connect(self._login)
        layout.addWidget(QLabel(APP_NAME))
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(submit)

    def _login(self) -> None:
        try:
            self.user = self.auth.login(self.username.text().strip(), self.password.text())
            log_action(self.user['id'], 'login_success', 'desktop_login')
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, 'خطأ', str(exc))


class ReceiptPage(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.editing_receipt_id = None
        self.tx_types = list_transaction_types()
        self.sample_types = list_sample_types()
        self.orgs = list_organizations(active_only=True)

        root = QVBoxLayout(self)
        form = QFormLayout()

        self.tx = QComboBox(); [self.tx.addItem(r['name'], r['id']) for r in self.tx_types]
        self.sender_org = QComboBox(); self.receiver_org = QComboBox()
        for o in self.orgs:
            self.sender_org.addItem(o['name'], o['id'])
            self.receiver_org.addItem(o['name'], o['id'])
        self.sender = QLineEdit(); self.receiver = QLineEdit()
        self.sender_job = QLineEdit(); self.receiver_job = QLineEdit()
        self.auth_no = QLineEdit(); self.auth_date = QLineEdit(); self.received_at = QLineEdit()
        self.notes = QTextEdit(); self.status = QComboBox(); self.status.addItems(['Draft', 'Approved', 'Rejected', 'Archived', 'Cancelled'])

        form.addRow('نوع المعاملة', self.tx)
        form.addRow('جهة الإرسال', self.sender_org)
        form.addRow('جهة الاستلام', self.receiver_org)
        form.addRow('اسم المرسل', self.sender)
        form.addRow('اسم المستلم', self.receiver)
        form.addRow('صفة المرسل', self.sender_job)
        form.addRow('صفة المستلم', self.receiver_job)
        form.addRow('رقم التخويل', self.auth_no)
        form.addRow('تاريخ التخويل', self.auth_date)
        form.addRow('وقت الاستلام', self.received_at)
        form.addRow('الحالة', self.status)
        form.addRow('ملاحظات', self.notes)

        root.addLayout(form)

        root.addWidget(QLabel('عناصر العينات'))
        self.items_table = QTableWidget(0, 9)
        self.items_table.setHorizontalHeaderLabels(['نوع العينة', 'المجموع', 'سليم', 'متضرر', 'مرفوض', 'غير مطابق', 'حالة النقل', 'ملاحظات', 'تحقق'])
        root.addWidget(self.items_table)

        row_buttons = QHBoxLayout()
        add_row = QPushButton('إضافة عنصر')
        add_row.clicked.connect(self.add_item_row)
        remove_row = QPushButton('حذف عنصر')
        remove_row.clicked.connect(self.remove_item_row)
        row_buttons.addWidget(add_row); row_buttons.addWidget(remove_row)
        root.addLayout(row_buttons)

        actions = QHBoxLayout()
        self.save_btn = QPushButton('حفظ إيصال جديد')
        self.save_btn.clicked.connect(self.save_receipt)
        self.update_btn = QPushButton('تحديث الإيصال')
        self.update_btn.clicked.connect(self.update_receipt)
        self.update_btn.setEnabled(False)
        self.clear_btn = QPushButton('تفريغ النموذج')
        self.clear_btn.clicked.connect(self.clear_form)
        actions.addWidget(self.save_btn); actions.addWidget(self.update_btn); actions.addWidget(self.clear_btn)
        root.addLayout(actions)

        self.add_item_row()

    def add_item_row(self):
        row = self.items_table.rowCount(); self.items_table.insertRow(row)
        combo = QComboBox(); [combo.addItem(s['name'], s['id']) for s in self.sample_types]
        self.items_table.setCellWidget(row, 0, combo)
        for col, val in [(1, '1'), (2, '1'), (3, '0'), (4, '0'), (5, '0'), (6, 'Normal'), (7, '')]:
            self.items_table.setItem(row, col, QTableWidgetItem(val))
        self.items_table.setItem(row, 8, QTableWidgetItem('✓'))

    def remove_item_row(self):
        row = self.items_table.currentRow()
        if row >= 0:
            self.items_table.removeRow(row)

    def _collect_items(self):
        items = []
        for r in range(self.items_table.rowCount()):
            combo = self.items_table.cellWidget(r, 0)
            item = {
                'sample_type_id': combo.currentData(),
                'total_count': int(self.items_table.item(r, 1).text()),
                'valid_count': int(self.items_table.item(r, 2).text()),
                'damaged_count': int(self.items_table.item(r, 3).text()),
                'rejected_count': int(self.items_table.item(r, 4).text()),
                'non_conforming_count': int(self.items_table.item(r, 5).text()),
                'transport_condition': self.items_table.item(r, 6).text(),
                'notes': self.items_table.item(r, 7).text(),
            }
            ok = item['total_count'] == item['valid_count'] + item['damaged_count'] + item['rejected_count'] + item['non_conforming_count']
            self.items_table.item(r, 8).setText('✓' if ok else '✗')
            if not ok:
                raise ValueError('فشل تحقق صف العينة')
            items.append(item)
        return items

    def _collect_header(self):
        return {
            'tx_type_id': self.tx.currentData(),
            'sender_org_id': self.sender_org.currentData(),
            'receiver_org_id': self.receiver_org.currentData(),
            'sender_name': self.sender.text().strip(),
            'receiver_name': self.receiver.text().strip(),
            'sender_job_title': self.sender_job.text().strip(),
            'receiver_job_title': self.receiver_job.text().strip(),
            'auth_doc_no': self.auth_no.text().strip(),
            'auth_date': self.auth_date.text().strip(),
            'received_at': self.received_at.text().strip(),
            'notes': self.notes.toPlainText(),
            'transport_info': '',
            'additional_comments': '',
            'status': self.status.currentText(),
        }

    def save_receipt(self):
        try:
            header = self._collect_header(); items = self._collect_items()
            rid, no = create_receipt(header, items, self.user['id'])
            QMessageBox.information(self, 'تم', f'تم إنشاء الإيصال: {no}')
            self.clear_form()
            log_action(self.user['id'], 'receipt_create_ui_success', f'{rid}')
        except Exception as exc:
            log_action(self.user['id'], 'receipt_create_ui_failed', str(exc))
            QMessageBox.warning(self, 'خطأ', str(exc))

    def load_receipt(self, receipt_id):
        header, items = get_receipt_details(receipt_id)
        if not header:
            return
        self.editing_receipt_id = receipt_id
        self.update_btn.setEnabled(True)
        self.save_btn.setEnabled(False)
        for c in range(self.tx.count()):
            if self.tx.itemData(c) == header['tx_type_id']: self.tx.setCurrentIndex(c)
        for c in range(self.sender_org.count()):
            if self.sender_org.itemData(c) == header['sender_org_id']: self.sender_org.setCurrentIndex(c)
        for c in range(self.receiver_org.count()):
            if self.receiver_org.itemData(c) == header['receiver_org_id']: self.receiver_org.setCurrentIndex(c)
        self.sender.setText(header['sender_name']); self.receiver.setText(header['receiver_name'])
        self.sender_job.setText(header['sender_job_title']); self.receiver_job.setText(header['receiver_job_title'])
        self.auth_no.setText(header['auth_doc_no']); self.auth_date.setText(header['auth_date'] or '')
        self.received_at.setText(header['received_at'] or ''); self.notes.setText(header['notes'] or '')
        self.status.setCurrentText(header['status'])
        self.items_table.setRowCount(0)
        for i in items:
            self.add_item_row()
            row = self.items_table.rowCount() - 1
            combo = self.items_table.cellWidget(row, 0)
            for c in range(combo.count()):
                if combo.itemData(c) == i['sample_type_id']: combo.setCurrentIndex(c)
            self.items_table.item(row, 1).setText(str(i['total_count']))
            self.items_table.item(row, 2).setText(str(i['valid_count']))
            self.items_table.item(row, 3).setText(str(i['damaged_count']))
            self.items_table.item(row, 4).setText(str(i['rejected_count']))
            self.items_table.item(row, 5).setText(str(i['non_conforming_count']))
            self.items_table.item(row, 6).setText(i['transport_condition'] or '')
            self.items_table.item(row, 7).setText(i['notes'] or '')

    def update_receipt(self):
        if not self.editing_receipt_id:
            return
        try:
            update_receipt(self.editing_receipt_id, self._collect_header(), self._collect_items(), self.user['id'])
            QMessageBox.information(self, 'تم', 'تم تحديث الإيصال')
        except Exception as exc:
            QMessageBox.warning(self, 'خطأ', str(exc))

    def clear_form(self):
        self.editing_receipt_id = None
        self.update_btn.setEnabled(False)
        self.save_btn.setEnabled(True)
        for w in [self.sender, self.receiver, self.sender_job, self.receiver_job, self.auth_no, self.auth_date, self.received_at]:
            w.clear()
        self.notes.clear()
        self.items_table.setRowCount(0)
        self.add_item_row()


class ArchivePage(QWidget):
    def __init__(self, user, receipt_page: ReceiptPage):
        super().__init__()
        self.user = user
        self.receipt_page = receipt_page
        layout = QVBoxLayout(self)
        filter_row = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText('بحث (رقم/مؤسسة/مستخدم/نوع)')
        self.status = QComboBox(); self.status.addItem('الكل', ''); self.status.addItems(['Draft', 'Approved', 'Rejected', 'Archived', 'Cancelled'])
        self.btn_search = QPushButton('بحث'); self.btn_search.clicked.connect(self.load_data)
        filter_row.addWidget(self.search); filter_row.addWidget(self.status); filter_row.addWidget(self.btn_search)
        layout.addLayout(filter_row)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(['ID', 'رقم الإيصال', 'التاريخ', 'المرسل', 'المستلم', 'الحالة', 'النوع'])
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        open_btn = QPushButton('فتح للتعديل'); open_btn.clicked.connect(self.open_selected)
        archive_btn = QPushButton('أرشفة'); archive_btn.clicked.connect(self.archive_selected)
        delete_btn = QPushButton('حذف منطقي'); delete_btn.clicked.connect(self.delete_selected)
        actions.addWidget(open_btn); actions.addWidget(archive_btn); actions.addWidget(delete_btn)
        layout.addLayout(actions)
        self.load_data()

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def load_data(self):
        rows = search_receipts(self.search.text().strip(), self.status.currentData())
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [r['id'], r['receipt_no'], r['created_at'], r['sender_org'], r['receiver_org'], r['status'], r['tx_type']]
            for j, v in enumerate(vals):
                self.table.setItem(i, j, QTableWidgetItem(str(v)))

    def open_selected(self):
        rid = self._selected_id()
        if not rid:
            return
        self.receipt_page.load_receipt(rid)

    def archive_selected(self):
        rid = self._selected_id()
        if not rid:
            return
        archive_receipt(rid, self.user['id'])
        self.load_data()

    def delete_selected(self):
        rid = self._selected_id()
        if not rid:
            return
        soft_delete_receipt(rid, self.user['id'])
        self.load_data()


class DashboardPage(QWidget):
    def __init__(self, user) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('لوحة التحكم الرئيسية'))
        layout.addWidget(QLabel(f'مرحباً {user["full_name"]} - الصلاحية: {user["role"]}'))


class MainWindow(QMainWindow):
    def __init__(self, user) -> None:
        super().__init__()
        self.user = user
        self.setWindowTitle(APP_NAME)
        self.resize(*DEFAULT_WINDOW_SIZE)
        self.setLayoutDirection(Qt.RightToLeft)
        root = QWidget(); shell = QHBoxLayout(root)
        sidebar = QListWidget(); sidebar.setFixedWidth(240)
        labels = ['لوحة التحكم', 'إدارة الإيصالات', 'أرشيف الإيصالات', 'الإعدادات', 'سجل التدقيق', 'النسخ الاحتياطي']
        for label in labels: sidebar.addItem(label)
        self.pages = QStackedWidget()
        self.receipt_page = ReceiptPage(user)
        self.archive_page = ArchivePage(user, self.receipt_page)
        self.pages.addWidget(DashboardPage(user))
        self.pages.addWidget(self.receipt_page)
        self.pages.addWidget(self.archive_page)
        self.pages.addWidget(QLabel('الإعدادات'))
        self.pages.addWidget(QLabel('سجل التدقيق'))
        self.pages.addWidget(QLabel('النسخ الاحتياطي'))
        sidebar.currentRowChanged.connect(self.pages.setCurrentIndex); sidebar.setCurrentRow(0)
        shell.addWidget(self.pages); shell.addWidget(sidebar)
        self.setCentralWidget(root)

    def load_archive(self):
        self.archive_page.load_data()


APP_STYLESHEET = f"""
QMainWindow, QWidget {{ background-color: {THEME['bg']}; color: {THEME['text']}; font-size: 13pt; }}
QPushButton {{ background-color: {THEME['primary']}; color: white; border: none; padding: 8px; min-height: 34px; }}
QLineEdit {{ background: {THEME['panel']}; border: 1px solid #CBD5E1; min-height: 34px; padding: 4px; }}
QListWidget {{ background: {THEME['panel']}; border: 1px solid #D1D5DB; }}
"""


def run() -> None:
    init_db(); seed_default_users(); seed_organizations(); seed_defaults()
    app = QApplication([]); app.setLayoutDirection(Qt.RightToLeft); app.setStyleSheet(APP_STYLESHEET)
    login = LoginWindow()
    if login.exec() != QDialog.Accepted or not login.user:
        return
    win = MainWindow(login.user); win.show(); app.exec()
