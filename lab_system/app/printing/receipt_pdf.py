"""
Enhanced Arabic governmental receipt PDF generation.

Supports:
- Arabic RTL layout with ReportLab
- Ministry-style header with logo
- Dynamic table of sample items
- QR code with receipt data
- Code128 barcode
- Signature sections
- A4 and thermal-friendly layout
"""

from datetime import datetime
from pathlib import Path

import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as RLImage,
)
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from lab_system.app.settings.config import STORAGE_DIR

# ---------------------------------------------------------------------------
# Font helpers — try to register Arabic TTF fonts; fall back to Helvetica
# ---------------------------------------------------------------------------
_ARABIC_FONTS = {
    "Arabic": None,
    "ArabicBold": None,
}

def _find_arabic_fonts():
    """Look for common Arabic TTF fonts on the system."""
    candidates = [
        "/usr/share/fonts/truetype/amiri/Amiri-Regular.ttf",
        "/usr/share/fonts/truetype/amiri/Amiri-Bold.ttf",
        "/usr/share/fonts/opentype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoNaskhArabic-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        p = Path(path)
        if p.exists():
            if "Bold" in p.name or "bold" in p.name:
                _ARABIC_FONTS["ArabicBold"] = str(p)
            else:
                _ARABIC_FONTS["Arabic"] = str(p)

_find_arabic_fonts()


def _register_fonts():
    """Register Arabic fonts with ReportLab if available."""
    if _ARABIC_FONTS["Arabic"]:
        try:
            pdfmetrics.registerFont(TTFont("Arabic", _ARABIC_FONTS["Arabic"]))
        except Exception:
            pass
    if _ARABIC_FONTS["ArabicBold"]:
        try:
            pdfmetrics.registerFont(TTFont("ArabicBold", _ARABIC_FONTS["ArabicBold"]))
        except Exception:
            pass


_register_fonts()


def _font_name(*, bold=False):
    if bold and "ArabicBold" in pdfmetrics.getRegisteredFontNames():
        return "ArabicBold"
    if "Arabic" in pdfmetrics.getRegisteredFontNames():
        return "Arabic"
    return "Helvetica-Bold" if bold else "Helvetica"


def _styles():
    """Return paragraph styles for the PDF."""
    fn = _font_name()
    fnb = _font_name(bold=True)
    return {
        "title": ParagraphStyle("Title", fontName=fnb, fontSize=16,
                                alignment=TA_CENTER, spaceAfter=6),
        "subtitle": ParagraphStyle("Subtitle", fontName=fn, fontSize=10,
                                   alignment=TA_CENTER, spaceAfter=4,
                                   textColor=colors.HexColor("#555555")),
        "meta_key": ParagraphStyle("MetaKey", fontName=fnb, fontSize=9,
                                   alignment=TA_RIGHT),
        "meta_val": ParagraphStyle("MetaVal", fontName=fn, fontSize=9,
                                   alignment=TA_RIGHT),
        "table_header": ParagraphStyle("TH", fontName=fnb, fontSize=8,
                                       alignment=TA_CENTER),
        "table_cell": ParagraphStyle("TC", fontName=fn, fontSize=8,
                                     alignment=TA_CENTER),
        "signature": ParagraphStyle("Sig", fontName=fn, fontSize=10,
                                    alignment=TA_CENTER, spaceBefore=20),
        "footer": ParagraphStyle("Footer", fontName=fn, fontSize=7,
                                 alignment=TA_CENTER,
                                 textColor=colors.HexColor("#999999")),
    }


def generate_receipt_pdf(receipt_no, institution, tx_type, date_text,
                         sender_name="", receiver_name="",
                         sender_org="", receiver_org="",
                         items=None, notes="", transport_info="",
                         logo_path=None):
    """
    Generate a production-quality Arabic governmental receipt PDF.

    Args:
        receipt_no: Receipt number string
        institution: Institution name
        tx_type: Transaction type name
        date_text: Date string for the receipt
        sender_name: Sender person name
        receiver_name: Receiver person name
        sender_org: Sender organization name
        receiver_org: Receiver organization name
        items: List of dicts with sample_name, total_count, valid_count,
               damaged_count, rejected_count, non_conforming_count,
               transport_condition, notes
        notes: Additional notes
        transport_info: Transport condition info
        logo_path: Optional path to organization logo image

    Returns:
        Path to the generated PDF file
    """
    pdf_path = STORAGE_DIR / "receipts" / f"{receipt_no}.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=20 * mm,
        bottomMargin=15 * mm,
        encoding="utf-8",
    )

    s = _styles()
    elements = []

    # ---- Header ----
    elements.append(Paragraph("نظام إدارة الاستلام المختبري", s["title"]))
    elements.append(Paragraph("إيصال رسمي", s["subtitle"]))
    elements.append(Spacer(1, 6 * mm))

    # ---- Logo (if provided) ----
    if logo_path and Path(logo_path).exists():
        try:
            img = RLImage(str(logo_path), width=3 * cm, height=3 * cm)
            elements.append(img)
        except Exception:
            pass

    # ---- Meta information table ----
    meta_data = [
        [Paragraph("رقم الإيصال", s["meta_key"]),
         Paragraph(receipt_no, s["meta_val"])],
        [Paragraph("نوع المعاملة", s["meta_key"]),
         Paragraph(tx_type, s["meta_val"])],
        [Paragraph("الجهة", s["meta_key"]),
         Paragraph(institution, s["meta_val"])],
        [Paragraph("التاريخ", s["meta_key"]),
         Paragraph(date_text, s["meta_val"])],
    ]
    if sender_org:
        meta_data.append([Paragraph("الجهة المرسلة", s["meta_key"]),
                          Paragraph(sender_org, s["meta_val"])])
    if receiver_org:
        meta_data.append([Paragraph("الجهة المستقبلة", s["meta_key"]),
                          Paragraph(receiver_org, s["meta_val"])])
    if sender_name:
        meta_data.append([Paragraph("المرسل", s["meta_key"]),
                          Paragraph(sender_name, s["meta_val"])])
    if receiver_name:
        meta_data.append([Paragraph("المستلم", s["meta_key"]),
                          Paragraph(receiver_name, s["meta_val"])])

    meta_table = Table(meta_data, colWidths=[doc.width * 0.3, doc.width * 0.7])
    meta_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#EEEEEE")),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 6 * mm))

    # ---- Items table ----
    if items and len(items) > 0:
        elements.append(Paragraph("العينات", s["subtitle"]))
        elements.append(Spacer(1, 2 * mm))

        header = ["نوع العينة", "المجموع", "صالح", "تالف", "مرفوض",
                  "غير مطابق", "حالة النقل"]
        table_data = [[Paragraph(h, s["table_header"]) for h in header]]

        for item in items:
            row = [
                Paragraph(str(item.get("sample_name", "")), s["table_cell"]),
                Paragraph(str(item.get("total_count", 0)), s["table_cell"]),
                Paragraph(str(item.get("valid_count", 0)), s["table_cell"]),
                Paragraph(str(item.get("damaged_count", 0)), s["table_cell"]),
                Paragraph(str(item.get("rejected_count", 0)), s["table_cell"]),
                Paragraph(str(item.get("non_conforming_count", 0)), s["table_cell"]),
                Paragraph(str(item.get("transport_condition", "")), s["table_cell"]),
            ]
            table_data.append(row)

        # Totals row
        total_row = ["الإجمالي"]
        for key in ["total_count", "valid_count", "damaged_count",
                     "rejected_count", "non_conforming_count"]:
            total_row.append(str(sum(int(it.get(key, 0)) for it in items)))
        total_row.append("")
        table_data.append([Paragraph(c, s["table_header"]) for c in total_row])

        col_widths = [doc.width * 0.18, doc.width * 0.10, doc.width * 0.10,
                      doc.width * 0.10, doc.width * 0.10, doc.width * 0.12,
                      doc.width * 0.20]
        item_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        item_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D4E89")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8F0FE")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F8FAFC")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(item_table)
        elements.append(Spacer(1, 4 * mm))

    # ---- Notes & transport ----
    if notes:
        elements.append(Paragraph(f"<b>ملاحظات:</b> {notes}", s["meta_val"]))
    if transport_info:
        elements.append(Paragraph(f"<b>معلومات النقل:</b> {transport_info}", s["meta_val"]))

    elements.append(Spacer(1, 10 * mm))

    # ---- QR Code ----
    temp_files = []
    try:
        qr_data = f"{receipt_no}|{institution}|{date_text}|{tx_type}"
        qr_img = qrcode.make(qr_data)
        import tempfile
        qr_tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        qr_tmp.close()
        qr_path = Path(qr_tmp.name)
        qr_img.save(str(qr_path))
        temp_files.append(qr_path)
        qr_rl = RLImage(str(qr_path), width=3 * cm, height=3 * cm)
        elements.append(qr_rl)
    except Exception:
        pass

    # ---- Barcode ----
    try:
        import tempfile
        bar_tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        bar_tmp.close()
        bar_path = Path(bar_tmp.name)
        with open(str(bar_path), "wb") as f:
            Code128(receipt_no, writer=ImageWriter()).write(f)
        temp_files.append(bar_path)
        bar_rl = RLImage(str(bar_path), width=8 * cm, height=1.5 * cm)
        elements.append(Spacer(1, 2 * mm))
        elements.append(bar_rl)
    except Exception:
        pass

    elements.append(Spacer(1, 10 * mm))

    # ---- Signature section ----
    sig_table = Table(
        [[Paragraph("توقيع المرسل: _____________", s["signature"]),
          Paragraph("توقيع المستلم: _____________", s["signature"])]],
        colWidths=[doc.width * 0.5, doc.width * 0.5],
    )
    sig_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(sig_table)

    # ---- Footer ----
    elements.append(Spacer(1, 8 * mm))
    elements.append(
        Paragraph(
            f"نظام إدارة الاستلام المختبري — الإصدار 1.0.0 — {datetime.now().year}",
            s["footer"],
        ),
    )

    # Build PDF
    doc.build(elements)
    for tf in temp_files:
        try:
            tf.unlink(missing_ok=True)
        except Exception:
            pass
    return pdf_path
