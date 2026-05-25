from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFormLayout, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox, QPushButton,
    QSpinBox, QStackedWidget, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget
)

from lab_system.app.audit.logger import log_action
from lab_system.app.database.db import init_db
from lab_system.app.services.auth_service import AuthService
from lab_system.app.services.catalog_service import list_sample_types, list_transaction_types, seed_defaults
from lab_system.app.services.org_service import list_organizations, search_organizations, set_organization_status, upsert_organization
from lab_system.app.services.receipt_service import (
    archive_receipt, create_receipt, get_receipt, search_receipts, soft_delete_receipt, update_receipt
)
from lab_system.app.services.seed_service import seed_organizations
from lab_system.app.services.user_service import seed_default_users
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
        layout.addWidget(QLabel(APP_NAME))
        self.username = QLineEdit(); self.username.setPlaceholderText('اسم المستخدم')
        self.password = QLineEdit(); self.password.setPlaceholderText('كلمة المرور'); self.password.setEchoMode(QLineEdit.Password)
        submit = QPushButton('دخول'); submit.clicked.connect(self._login)
        layout.addWidget(self.username); layout.addWidget(self.password); layout.addWidget(submit)

    def _login(self) -> None:
        try:
            self.user = self.auth.login(self.username.text().strip(), self.password.text())
            log_action(self.user['id'], 'login_success', 'desktop_login')
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, 'خطأ', str(exc))


class ReceiptFormPage(QWidget):
    def __init__(self, user, on_saved):
        super().__init__()
        self.user = user
        self.on_saved = on_saved
        self.edit_receipt_id = None
        self.tx_types = list_transaction_types()
        self.sample_types = list_sample_types()
        self.orgs = list_organizations(active_only=True)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        form = QGridLayout()
        self.tx = QComboBox(); [self.tx.addItem(r['name'], r['id']) for r in self.tx_types]
        self.sender_org = QComboBox(); self.receiver_org = QComboBox()
        for o in self.orgs:
            self.sender_org.addItem(o['name'], o['id']); self.receiver_org.addItem(o['name'], o['id'])
        self.sender_name = QLineEdit(); self.receiver_name = QLineEdit()
        self.sender_job = QLineEdit(); self.receiver_job = QLineEdit()
        self.auth_doc = QLineEdit(); self.auth_date = QLineEdit(); self.received_at = QLineEdit()
        self.status = QComboBox(); self.status.addItems(['Draft', 'Approved', 'Rejected', 'Archived', 'Cancelled'])
        self.notes = QTextEdit()

        fields = [
            ('نوع المعاملة', self.tx), ('جهة الإرسال', self.sender_org), ('جهة الاستلام', self.receiver_org),
            ('اسم المرسل', self.sender_name), ('اسم المستلم', self.receiver_name),
            ('صفة المرسل', self.sender_job), ('صفة المستلم', self.receiver_job),
            ('رقم التخويل', self.auth_doc), ('تاريخ التخويل', self.auth_date), ('تاريخ/وقت الاستلام', self.received_at),
            ('الحالة', self.status), ('ملاحظات', self.notes),
        ]
        for i, (label, w) in enumerate(fields):
            form.addWidget(QLabel(label), i, 0); form.addWidget(w, i, 1)

        layout.addLayout(form)

        self.items_table = QTableWidget(0, 9)
        self.items_table.setHorizontalHeaderLabels(['نوع العينة', 'المجموع', 'سليم', 'متضرر', 'مرفوض', 'غير مطابق', 'النقل', 'ملاحظات', ''])
        layout.addWidget(QLabel('العينات'))
        layout.addWidget(self.items_table)

        add_btn = QPushButton('إضافة عنصر'); add_btn.clicked.connect(self.add_item_row)
        save_btn = QPushButton('حفظ الإيصال'); save_btn.clicked.connect(self.save_receipt)
        clear_btn = QPushButton('جديد'); clear_btn.clicked.connect(self.reset_form)
        h = QHBoxLayout(); h.addWidget(add_btn); h.addWidget(save_btn); h.addWidget(clear_btn)
        layout.addLayout(h)
        self.add_item_row()

    def add_item_row(self, item_data=None):
        row = self.items_table.rowCount(); self.items_table.insertRow(row)
        sample = QComboBox(); [sample.addItem(s['name'], s['id']) for s in self.sample_types]
        self.items_table.setCellWidget(row, 0, sample)
        vals = [1, 1, 0, 0, 0]
        if item_data:
            vals = [item_data['total_count'], item_data['valid_count'], item_data['damaged_count'], item_data['rejected_count'], item_data['non_conforming_count']]
        for c, v in enumerate(vals, 1):
            sp = QSpinBox(); sp.setRange(0, 100000); sp.setValue(v); self.items_table.setCellWidget(row, c, sp)
        self.items_table.setItem(row, 6, QTableWidgetItem(item_data['transport_condition'] if item_data else ''))
        self.items_table.setItem(row, 7, QTableWidgetItem(item_data['notes'] if item_data else ''))
        rm = QPushButton('حذف'); rm.clicked.connect(lambda: self.items_table.removeRow(self.items_table.indexAt(rm.pos()).row()))
        self.items_table.setCellWidget(row, 8, rm)

    def _collect_items(self):
        items = []
        for r in range(self.items_table.rowCount()):
            sample = self.items_table.cellWidget(r, 0)
            get = lambda c: self.items_table.cellWidget(r, c).value()
            transport = self.items_table.item(r, 6).text() if self.items_table.item(r, 6) else ''
            notes = self.items_table.item(r, 7).text() if self.items_table.item(r, 7) else ''
            items.append({'sample_type_id': sample.currentData(), 'total_count': get(1), 'valid_count': get(2), 'damaged_count': get(3), 'rejected_count': get(4), 'non_conforming_count': get(5), 'transport_condition': transport, 'notes': notes})
        return items

    def _collect_data(self):
        return {
            'tx_type_id': self.tx.currentData(), 'sender_org_id': self.sender_org.currentData(), 'receiver_org_id': self.receiver_org.currentData(),
            'sender_name': self.sender_name.text(), 'receiver_name': self.receiver_name.text(), 'sender_job_title': self.sender_job.text(),
            'receiver_job_title': self.receiver_job.text(), 'auth_doc_no': self.auth_doc.text(), 'auth_date': self.auth_date.text(),
            'received_at': self.received_at.text(), 'notes': self.notes.toPlainText(), 'status': self.status.currentText(),
        }

    def save_receipt(self):
        try:
            data = self._collect_data(); items = self._collect_items()
            if self.edit_receipt_id:
                update_receipt(self.edit_receipt_id, data, items, self.user['id'])
                log_action(self.user['id'], 'receipt_updated', str(self.edit_receipt_id))
                QMessageBox.information(self, 'تم', 'تم تحديث الإيصال')
            else:
                rid, no = create_receipt(data, items, self.user['id'])
                log_action(self.user['id'], 'receipt_created', f'{rid}:{no}')
                QMessageBox.information(self, 'تم', f'تم حفظ الإيصال {no}')
            self.reset_form(); self.on_saved()
        except Exception as exc:
            log_action(self.user['id'], 'receipt_save_failed', str(exc))
            QMessageBox.warning(self, 'خطأ', str(exc))

    def load_receipt(self, receipt_id: int):
        receipt, items = get_receipt(receipt_id)
        if not receipt:
            return
        self.edit_receipt_id = receipt_id
        for i in range(self.tx.count()):
            if self.tx.itemData(i) == receipt['tx_type_id']: self.tx.setCurrentIndex(i)
        for cb, val in [(self.sender_org, receipt['sender_org_id']), (self.receiver_org, receipt['receiver_org_id'])]:
            for i in range(cb.count()):
                if cb.itemData(i) == val: cb.setCurrentIndex(i)
        self.sender_name.setText(receipt['sender_name']); self.receiver_name.setText(receipt['receiver_name'])
        self.sender_job.setText(receipt['sender_job_title'] or ''); self.receiver_job.setText(receipt['receiver_job_title'] or '')
        self.auth_doc.setText(receipt['auth_doc_no'] or ''); self.auth_date.setText(receipt['auth_date'] or '')
        self.received_at.setText(receipt['received_at'] or '')
        self.notes.setPlainText(receipt['notes'] or ''); self.status.setCurrentText(receipt['status'])
        self.items_table.setRowCount(0)
        for item in items: self.add_item_row(item)

    def reset_form(self):
        self.edit_receipt_id = None
        self.sender_name.clear(); self.receiver_name.clear(); self.sender_job.clear(); self.receiver_job.clear()
        self.auth_doc.clear(); self.auth_date.clear(); self.received_at.clear(); self.notes.clear(); self.status.setCurrentText('Draft')
        self.items_table.setRowCount(0); self.add_item_row()


class ReceiptArchivePage(QWidget):
    def __init__(self, user, on_open):
        super().__init__(); self.user = user; self.on_open = on_open
        l = QVBoxLayout(self)
        h = QHBoxLayout(); self.search = QLineEdit(); self.search.setPlaceholderText('بحث برقم/مؤسسة/نوع/مستخدم')
        self.status = QComboBox(); self.status.addItems(['', 'Draft', 'Approved', 'Rejected', 'Archived', 'Cancelled'])
        btn = QPushButton('بحث'); btn.clicked.connect(self.load_rows)
        h.addWidget(self.search); h.addWidget(self.status); h.addWidget(btn); l.addLayout(h)
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(['ID', 'رقم', 'التاريخ', 'المرسل', 'المستلم', 'الحالة', 'النوع', 'المستخدم', 'إجراءات'])
        l.addWidget(self.table)
        self.load_rows()

    def load_rows(self):
        rows, _ = search_receipts({'q': self.search.text(), 'status': self.status.currentText()})
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            data = [row['id'], row['receipt_no'], row['received_at'] or row['created_at'], row['sender_org'], row['receiver_org'], row['status'], row['tx_type'], row['created_by_name'] or '-']
            for c, v in enumerate(data): self.table.setItem(r, c, QTableWidgetItem(str(v)))
            ops = QWidget(); h = QHBoxLayout(ops); h.setContentsMargins(0, 0, 0, 0)
            open_b = QPushButton('فتح'); open_b.clicked.connect(lambda _, rid=row['id']: self.on_open(rid))
            arch_b = QPushButton('أرشفة'); arch_b.clicked.connect(lambda _, rid=row['id']: self._archive(rid))
            del_b = QPushButton('حذف'); del_b.clicked.connect(lambda _, rid=row['id']: self._delete(rid))
            h.addWidget(open_b); h.addWidget(arch_b); h.addWidget(del_b)
            self.table.setCellWidget(r, 8, ops)

    def _archive(self, rid):
        archive_receipt(rid, self.user['id']); log_action(self.user['id'], 'receipt_archived', str(rid)); self.load_rows()

    def _delete(self, rid):
        soft_delete_receipt(rid, self.user['id']); log_action(self.user['id'], 'receipt_soft_deleted', str(rid)); self.load_rows()


class InstitutionsPage(QWidget):
    def __init__(self, user):
        super().__init__(); self.user = user; self.edit_id = None
        l = QVBoxLayout(self)
        top = QHBoxLayout(); self.search = QLineEdit(); self.search.setPlaceholderText('بحث مؤسسة')
        self.status_filter = QComboBox(); self.status_filter.addItems(['', 'Active', 'Inactive'])
        btn = QPushButton('بحث'); btn.clicked.connect(self.load_rows)
        top.addWidget(self.search); top.addWidget(self.status_filter); top.addWidget(btn); l.addLayout(top)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(['ID','الاسم','الرمز','النوع','المحافظة','الحالة'])
        self.table.cellClicked.connect(self.select_row)
        l.addWidget(self.table)

        f = QGridLayout()
        self.name = QLineEdit(); self.code = QLineEdit(); self.org_type = QComboBox(); self.org_type.addItems(['Hospital','Public Health Laboratory','Central Laboratory','Primary Healthcare Center','Blood Bank','Referral Center','Private Laboratory','Other'])
        self.gov = QLineEdit(); self.addr = QLineEdit(); self.phone = QLineEdit(); self.email = QLineEdit()
        self.notes = QTextEdit(); self.status = QComboBox(); self.status.addItems(['Active','Inactive'])
        fields=[('الاسم',self.name),('الرمز',self.code),('النوع',self.org_type),('المحافظة',self.gov),('العنوان',self.addr),('الهاتف',self.phone),('البريد',self.email),('الحالة',self.status),('ملاحظات',self.notes)]
        for i,(n,w) in enumerate(fields): f.addWidget(QLabel(n),i,0); f.addWidget(w,i,1)
        l.addLayout(f)

        a=QHBoxLayout(); save=QPushButton('حفظ المؤسسة'); save.clicked.connect(self.save_org)
        archive=QPushButton('أرشفة'); archive.clicked.connect(self.archive_selected)
        new=QPushButton('جديد'); new.clicked.connect(self.reset_form)
        a.addWidget(save); a.addWidget(archive); a.addWidget(new); l.addLayout(a)
        self.load_rows()

    def load_rows(self):
        rows = search_organizations(self.search.text(), self.status_filter.currentText())
        self.table.setRowCount(len(rows))
        for r,row in enumerate(rows):
            vals=[row['id'],row['name'],row['code'],row['org_type'],row['governorate'],row['status']]
            for c,v in enumerate(vals): self.table.setItem(r,c,QTableWidgetItem(str(v)))

    def select_row(self,row,_):
        self.edit_id = int(self.table.item(row,0).text())
        self.name.setText(self.table.item(row,1).text()); self.code.setText(self.table.item(row,2).text())
        self.gov.setText(self.table.item(row,4).text()); self.status.setCurrentText(self.table.item(row,5).text())

    def save_org(self):
        try:
            payload={'id':self.edit_id,'name':self.name.text(),'code':self.code.text(),'org_type':self.org_type.currentText(),'governorate':self.gov.text(),'address':self.addr.text(),'phone':self.phone.text(),'email':self.email.text(),'logo_path':'','notes':self.notes.toPlainText(),'status':self.status.currentText()}
            org_id=upsert_organization(payload)
            log_action(self.user['id'],'organization_upsert',str(org_id))
            self.load_rows(); self.reset_form(); QMessageBox.information(self,'تم','تم حفظ المؤسسة')
        except Exception as exc:
            QMessageBox.warning(self,'خطأ',str(exc))

    def archive_selected(self):
        if not self.edit_id: return
        set_organization_status(self.edit_id,'Archived')
        log_action(self.user['id'],'organization_archived',str(self.edit_id))
        self.load_rows(); self.reset_form()

    def reset_form(self):
        self.edit_id=None
        self.name.clear(); self.code.clear(); self.gov.clear(); self.addr.clear(); self.phone.clear(); self.email.clear(); self.notes.clear(); self.status.setCurrentText('Active')


class MainWindow(QMainWindow):
    def __init__(self, user) -> None:
        super().__init__(); self.user = user
        self.setWindowTitle(APP_NAME); self.resize(*DEFAULT_WINDOW_SIZE); self.setLayoutDirection(Qt.RightToLeft)
        root = QWidget(); shell = QHBoxLayout(root)
        self.sidebar = QListWidget(); self.sidebar.setFixedWidth(240)
        self.pages = QStackedWidget()

        self.receipt_form = ReceiptFormPage(user, self._refresh_archive)
        self.receipt_archive = ReceiptArchivePage(user, self._open_receipt)

        self.institutions_page = InstitutionsPage(user)
        items = [
            ('dashboard', QLabel(f'مرحباً {user["full_name"]}')),
            ('new_receipt', self.receipt_form),
            ('receipt_archive', self.receipt_archive),
            ('institutions', self.institutions_page),
            ('settings', QLabel('الإعدادات')),
            ('audit', QLabel('سجل التدقيق')),
        ]
        for _, w in items:
            page = QWidget(); v = QVBoxLayout(page); v.addWidget(w); self.pages.addWidget(page)
        for name in ['لوحة التحكم', 'إيصال جديد', 'أرشيف الإيصالات', 'إدارة المؤسسات', 'الإعدادات', 'سجل التدقيق']:
            self.sidebar.addItem(name)

        self.sidebar.currentRowChanged.connect(self.pages.setCurrentIndex); self.sidebar.setCurrentRow(0)
        panel = QFrame(); pv = QVBoxLayout(panel); pv.addWidget(self.pages)
        shell.addWidget(panel); shell.addWidget(self.sidebar); self.setCentralWidget(root)

    def _refresh_archive(self): self.receipt_archive.load_rows()

    def _open_receipt(self, rid):
        self.receipt_form.load_receipt(rid)
        self.sidebar.setCurrentRow(1)


APP_STYLESHEET = f"""
QMainWindow, QWidget {{ background-color: {THEME['bg']}; color: {THEME['text']}; font-size: 12pt; }}
QPushButton {{ background-color: {THEME['primary']}; color: white; border: none; padding: 6px; min-height: 30px; }}
QLineEdit, QComboBox, QSpinBox, QTextEdit {{ background: {THEME['panel']}; border: 1px solid #CBD5E1; min-height: 30px; padding: 4px; }}
QListWidget {{ background: {THEME['panel']}; border: 1px solid #D1D5DB; }}
"""


def run() -> None:
    init_db(); seed_default_users(); seed_organizations(); seed_defaults()
    app = QApplication([]); app.setLayoutDirection(Qt.RightToLeft); app.setStyleSheet(APP_STYLESHEET)
    login = LoginWindow()
    if login.exec() != QDialog.Accepted or not login.user: return
    win = MainWindow(login.user); win.show(); app.exec()
