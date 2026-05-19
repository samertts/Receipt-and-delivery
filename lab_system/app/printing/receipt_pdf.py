from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from lab_system.app.settings.config import STORAGE_DIR

def generate_receipt_pdf(receipt_no, institution, tx_type, date_text):
    pdf_path = STORAGE_DIR / 'receipts' / f'{receipt_no}.pdf'
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    c.setFont('Helvetica-Bold', 16)
    c.drawString(120, 800, 'نظام إدارة الاستلام المختبري - إيصال رسمي')
    c.setFont('Helvetica', 12)
    c.drawString(50, 760, f'Receipt: {receipt_no}')
    c.drawString(50, 740, f'Institution: {institution}')
    c.drawString(50, 720, f'Type: {tx_type}')
    c.drawString(50, 700, f'Date: {date_text}')
    qr_file = STORAGE_DIR / 'temp' / f'{receipt_no}_qr.png'
    qrcode.make(f'{receipt_no}|{institution}|{date_text}|{tx_type}').save(qr_file)
    bar_file = STORAGE_DIR / 'temp' / f'{receipt_no}_bar'
    Code128(receipt_no, writer=ImageWriter()).write(open(f'{bar_file}.png', 'wb'))
    c.drawImage(str(qr_file), 430, 690, width=120, height=120)
    c.drawImage(f'{bar_file}.png', 50, 640, width=280, height=45)
    c.drawString(50, 120, 'توقيع المرسل: _____________')
    c.drawString(320, 120, 'توقيع المستلم: _____________')
    c.save()
    return Path(pdf_path)
