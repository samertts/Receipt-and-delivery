from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QTabWidget, QFormLayout, QComboBox, QTextEdit, QMessageBox
from PySide6.QtCore import Qt
from lab_system.app.database.db import init_db, get_conn
from lab_system.app.services.user_service import seed_default_users, authenticate
from lab_system.app.services.seed_service import seed_organizations
from lab_system.app.services.receipt_service import create_receipt
from lab_system.app.audit.logger import log_action

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__(); self.user=None
        self.setWindowTitle('تسجيل الدخول')
        self.setLayoutDirection(Qt.RightToLeft)
        layout = QVBoxLayout(self)
        self.u=QLineEdit(); self.u.setPlaceholderText('اسم المستخدم')
        self.p=QLineEdit(); self.p.setEchoMode(QLineEdit.Password); self.p.setPlaceholderText('كلمة المرور')
        btn=QPushButton('دخول')
        btn.clicked.connect(self.do_login)
        layout.addWidget(QLabel('نظام إدارة الاستلام المختبري'))
        layout.addWidget(self.u); layout.addWidget(self.p); layout.addWidget(btn)
    def do_login(self):
        row=authenticate(self.u.text().strip(), self.p.text())
        if not row:
            QMessageBox.warning(self,'خطأ','بيانات دخول غير صحيحة'); return
        self.user=row; log_action(row['id'],'login_success'); self.close()

class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__(); self.user=user
        self.setWindowTitle('نظام إدارة الاستلام المختبري')
        self.resize(1100, 700)
        self.setLayoutDirection(Qt.RightToLeft)
        tabs=QTabWidget(); self.setCentralWidget(tabs)
        tabs.addTab(self.dashboard_tab(),'لوحة التحكم')
        tabs.addTab(self.new_receipt_tab(),'استلام جديد')
        for name in ['أرشيف الإيصالات','تفاصيل الإيصال','التقارير','المؤسسات','المرفقات','الإعدادات','سجل التدقيق','النسخ الاحتياطي والاستعادة']:
            w=QWidget(); l=QVBoxLayout(w); l.addWidget(QLabel(f'نافذة {name} (جاهزة للتوسعة)')); tabs.addTab(w,name)
    def dashboard_tab(self):
        w=QWidget(); l=QVBoxLayout(w)
        with get_conn() as conn: count = conn.execute('SELECT COUNT(*) c FROM receipts').fetchone()['c']
        l.addWidget(QLabel(f'مرحباً {self.user["full_name"]} | عدد الإيصالات: {count}'))
        return w
    def new_receipt_tab(self):
        w=QWidget(); f=QFormLayout(w)
        self.tx=QComboBox(); self.tx.addItems(['sample_receipt','sample_delivery','referral_transfer','material_transfer'])
        self.sender_org=QLineEdit('1'); self.receiver_org=QLineEdit('2')
        self.sender=QLineEdit(); self.receiver=QLineEdit(); self.auth=QLineEdit(); self.auth_date=QLineEdit(); self.notes=QTextEdit(); self.status=QComboBox(); self.status.addItems(['Draft','Approved','Rejected','Archived','Cancelled'])
        save=QPushButton('حفظ الإيصال'); save.clicked.connect(self.save_receipt)
        for lbl,widget in [('نوع المعاملة',self.tx),('جهة الإرسال (ID)',self.sender_org),('جهة الاستلام (ID)',self.receiver_org),('اسم المرسل',self.sender),('اسم المستلم',self.receiver),('رقم التخويل',self.auth),('تاريخ التخويل',self.auth_date),('ملاحظات',self.notes),('الحالة',self.status)]: f.addRow(lbl,widget)
        f.addRow(save)
        return w
    def save_receipt(self):
        data={'tx_type':self.tx.currentText(),'sender_org_id':int(self.sender_org.text()),'receiver_org_id':int(self.receiver_org.text()),'sender_name':self.sender.text(),'receiver_name':self.receiver.text(),'auth_doc_no':self.auth.text(),'auth_date':self.auth_date.text(),'notes':self.notes.toPlainText(),'status':self.status.currentText()}
        items=[{'sample_type':'default','total_count':1,'valid_count':1,'damaged_count':0,'rejected_count':0,'non_conforming_count':0,'transport_condition':'normal','notes':''}]
        rid=create_receipt(data,items,self.user['id']); log_action(self.user['id'],'receipt_created',f'receipt_id={rid}')
        QMessageBox.information(self,'تم',f'تم حفظ الإيصال رقم داخلي {rid}')

def run():
    init_db(); seed_default_users(); seed_organizations()
    app=QApplication([])
    app.setLayoutDirection(Qt.RightToLeft)
    login=LoginWindow(); login.show(); app.exec()
    if login.user:
        mw=MainWindow(login.user); mw.show(); app.exec()
