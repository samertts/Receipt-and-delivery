from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QTabWidget, QFormLayout, QComboBox, QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt
from lab_system.app.database.db import init_db
from lab_system.app.services.user_service import seed_default_users, authenticate, list_users, create_user
from lab_system.app.services.seed_service import seed_organizations
from lab_system.app.services.catalog_service import seed_defaults, list_transaction_types, list_sample_types
from lab_system.app.services.org_service import list_organizations
from lab_system.app.services.receipt_service import create_receipt, search_receipts
from lab_system.app.audit.logger import log_action

from PySide6.QtWidgets import QDialog

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__(); self.user = None
        self.setWindowTitle('تسجيل الدخول'); self.setLayoutDirection(Qt.RightToLeft)
        l = QVBoxLayout(self)
        self.u = QLineEdit(); self.u.setPlaceholderText('اسم المستخدم')
        self.p = QLineEdit(); self.p.setEchoMode(QLineEdit.Password); self.p.setPlaceholderText('كلمة المرور')
        b = QPushButton('دخول'); b.clicked.connect(self.do_login)
        l.addWidget(QLabel('نظام إدارة الاستلام المختبري')); l.addWidget(self.u); l.addWidget(self.p); l.addWidget(b)
    def do_login(self):
        row = authenticate(self.u.text().strip(), self.p.text())
        if not row: QMessageBox.warning(self, 'خطأ', 'بيانات دخول غير صحيحة'); return
        self.user = row
        log_action(row['id'], 'login_success')
        self.accept()

class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__(); self.user = user
        self.setWindowTitle('نظام إدارة الاستلام المختبري'); self.resize(1200, 760); self.setLayoutDirection(Qt.RightToLeft)
        self.orgs = list_organizations(active_only=True); self.tx_types = list_transaction_types(); self.sample_types = list_sample_types()
        tabs = QTabWidget(); self.setCentralWidget(tabs)
        tabs.addTab(self.dashboard_tab(), 'لوحة التحكم'); tabs.addTab(self.new_receipt_tab(), 'استلام جديد')
        tabs.addTab(self.archive_tab(), 'أرشيف الإيصالات'); tabs.addTab(self.users_tab(), 'إدارة المستخدمين')
        for name in ['التقارير', 'المؤسسات', 'المرفقات', 'الإعدادات', 'سجل التدقيق', 'النسخ الاحتياطي والاستعادة', 'مصمم النماذج']:
            w = QWidget(); x = QVBoxLayout(w); x.addWidget(QLabel(f'نافذة {name}')); tabs.addTab(w, name)
    def dashboard_tab(self):
        w = QWidget(); l = QVBoxLayout(w); l.addWidget(QLabel(f'مرحباً {self.user["full_name"]} ({self.user["role"]})')); return w
    def new_receipt_tab(self):
        w = QWidget(); f = QFormLayout(w)
        self.tx = QComboBox(); [self.tx.addItem(r['name'], r['id']) for r in self.tx_types]
        self.sender_org = QComboBox(); self.receiver_org = QComboBox()
        for o in self.orgs: self.sender_org.addItem(o['name'], o['id']); self.receiver_org.addItem(o['name'], o['id'])
        self.sample = QComboBox(); [self.sample.addItem(r['name'], r['id']) for r in self.sample_types]
        self.sender = QLineEdit(); self.receiver = QLineEdit(); self.sender_job = QLineEdit(); self.receiver_job = QLineEdit(); self.auth = QLineEdit(); self.auth_date = QLineEdit(); self.notes = QTextEdit(); self.status = QComboBox(); self.status.addItems(['Draft','Approved','Rejected','Archived','Cancelled'])
        self.total = QLineEdit('1'); self.valid = QLineEdit('1'); self.damaged = QLineEdit('0'); self.rejected = QLineEdit('0'); self.nonc = QLineEdit('0')
        save = QPushButton('حفظ الإيصال'); save.clicked.connect(self.save_receipt)
        for lbl, wd in [('نوع المعاملة', self.tx), ('جهة الإرسال', self.sender_org), ('جهة الاستلام', self.receiver_org), ('اسم المرسل', self.sender), ('اسم المستلم', self.receiver), ('صفة المرسل', self.sender_job), ('صفة المستلم', self.receiver_job), ('رقم التخويل', self.auth), ('تاريخ التخويل', self.auth_date), ('العينة', self.sample), ('المجموع', self.total), ('سليم', self.valid), ('متضرر', self.damaged), ('مرفوض', self.rejected), ('غير مطابق', self.nonc), ('ملاحظات', self.notes), ('الحالة', self.status)]: f.addRow(lbl, wd)
        f.addRow(save); return w
    def save_receipt(self):
        try:
            item = {'sample_type_id': self.sample.currentData(), 'total_count': int(self.total.text()), 'valid_count': int(self.valid.text()), 'damaged_count': int(self.damaged.text()), 'rejected_count': int(self.rejected.text()), 'non_conforming_count': int(self.nonc.text()), 'transport_condition': 'Normal', 'notes': ''}
            data = {'tx_type_id': self.tx.currentData(), 'sender_org_id': self.sender_org.currentData(), 'receiver_org_id': self.receiver_org.currentData(), 'sender_name': self.sender.text().strip(), 'receiver_name': self.receiver.text().strip(), 'sender_job_title': self.sender_job.text().strip(), 'receiver_job_title': self.receiver_job.text().strip(), 'auth_doc_no': self.auth.text().strip(), 'auth_date': self.auth_date.text().strip(), 'notes': self.notes.toPlainText(), 'transport_info': '', 'additional_comments': '', 'status': self.status.currentText()}
            if not data['sender_name'] or not data['receiver_name']: raise ValueError('الاسم مطلوب')
            rid, no = create_receipt(data, [item], self.user['id'])
            log_action(self.user['id'], 'receipt_created', f'receipt_id={rid}')
            QMessageBox.information(self, 'تم', f'تم حفظ الإيصال {no}')
            self.load_archive()
        except Exception as exc:
            QMessageBox.warning(self, 'خطأ', str(exc))
    def archive_tab(self):
        w = QWidget(); l = QVBoxLayout(w); self.search = QLineEdit(); self.search.setPlaceholderText('بحث برقم أو مؤسسة'); self.search.textChanged.connect(self.load_archive)
        self.table = QTableWidget(0, 5); self.table.setHorizontalHeaderLabels(['رقم الإيصال', 'النوع', 'المرسل', 'المستلم', 'التاريخ'])
        l.addWidget(self.search); l.addWidget(self.table); self.load_archive(); return w
    def load_archive(self):
        rows = search_receipts(self.search.text().strip(), 1, 100)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(['receipt_no', 'tx_type', 'sender_org', 'receiver_org', 'created_at']): self.table.setItem(i, j, QTableWidgetItem(str(r[k])))
    def users_tab(self):
        w = QWidget(); l = QVBoxLayout(w)
        self.users_table = QTableWidget(0, 4); self.users_table.setHorizontalHeaderLabels(['المستخدم', 'الاسم', 'الدور', 'الحالة'])
        form = QFormLayout(); self.uf = QLineEdit(); self.uu = QLineEdit(); self.up = QLineEdit(); self.ur = QComboBox(); self.ur.addItems(['Admin','Supervisor','User','Auditor'])
        b = QPushButton('إضافة مستخدم'); b.clicked.connect(self.add_user)
        for n, wd in [('الاسم الكامل', self.uf), ('اسم المستخدم', self.uu), ('كلمة المرور', self.up), ('الدور', self.ur)]: form.addRow(n, wd)
        l.addWidget(self.users_table); l.addLayout(form); l.addWidget(b); self.load_users(); return w
    def load_users(self):
        rows = list_users(); self.users_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.users_table.setItem(i, 0, QTableWidgetItem(r['username'])); self.users_table.setItem(i, 1, QTableWidgetItem(r['full_name'])); self.users_table.setItem(i, 2, QTableWidgetItem(r['role'])); self.users_table.setItem(i, 3, QTableWidgetItem(r['status']))
    def add_user(self):
        if self.user['role'] != 'Admin': QMessageBox.warning(self, 'رفض', 'فقط المدير'); return
        create_user(self.uf.text().strip(), self.uu.text().strip(), self.up.text().strip(), self.ur.currentText())
        log_action(self.user['id'], 'user_created', self.uu.text().strip()); self.load_users(); QMessageBox.information(self, 'تم', 'تمت الإضافة')

def run():
    init_db(); seed_default_users(); seed_organizations(); seed_defaults()
    app = QApplication([])
    app.setLayoutDirection(Qt.RightToLeft)
    login = LoginWindow()
    if login.exec() != 1 or not login.user:
        return

    mw = MainWindow(login.user)
    mw.show()
    app.exec()
