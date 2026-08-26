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
import os
import re
import tempfile
from pathlib import Path

import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, A5, landscape
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
from pypdf import PdfReader, PdfWriter

from lab_system.app.settings.config import CONFIG, STORAGE_DIR

# ---------------------------------------------------------------------------
# Font helpers — try to register Arabic TTF fonts; fall back to Helvetica
# ---------------------------------------------------------------------------
def format_receipt_datetime(value):
    """Format ISO/date-time values without inventing an unavailable timezone."""
    if value in (None, ""):
        return ""
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            return ""
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return text
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _display_text(value):
    """Shape Arabic and apply bidirectional display order for ReportLab."""
    text = str(value or "")
    if not re.search(r"[\u0600-\u06FF]", text):
        return text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display

        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


_ARABIC_FONTS = {
    "Arabic": None,
    "ArabicBold": None,
}


def _find_arabic_fonts():
    """Look for common Arabic TTF fonts on the system."""
    from sys import platform as _sys_platform

    candidates = [
        "/usr/share/fonts/truetype/amiri/Amiri-Regular.ttf",
        "/usr/share/fonts/truetype/amiri/Amiri-Bold.ttf",
        "/usr/share/fonts/opentype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoNaskhArabic-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    if _sys_platform == "win32":
        win_dir = Path("C:/Windows/Fonts")
        candidates += [
            str(win_dir / "amiri" / "amiri-regular.ttf"),
            str(win_dir / "amiri" / "amiri-bold.ttf"),
            str(win_dir / "NotoNaskhArabic" / "NotoNaskhArabic-Regular.ttf"),
            str(win_dir / "NotoNaskhArabic" / "NotoNaskhArabic-Bold.ttf"),
            str(win_dir / "DejaVuSans.ttf"),
            str(win_dir / "DejaVuSans-Bold.ttf"),
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


def _safe_hex_color(value, fallback="#1D4E89"):
    value = str(value or "").strip()
    return value if re.fullmatch(r"#[0-9A-Fa-f]{6}", value) else fallback


def _default_logo_path():
    candidates = [
        os.environ.get("LAB_RECEIPT_LOGO_PATH", ""),
        str(CONFIG.storage_dir / "settings" / "company_logo.png"),
        str(CONFIG.assets_dir / "company_logo.png"),
        str(CONFIG.assets_dir / "logo.png"),
    ]
    return next((path for path in candidates if path and Path(path).is_file()), None)


def _styles(primary_color="#1D4E89", compact=False):
    """Return paragraph styles for the PDF."""
    primary_color = _safe_hex_color(primary_color)
    fn = _font_name()
    fnb = _font_name(bold=True)
    styles = {
        "title": ParagraphStyle(
            "Title",             fontName=fnb, fontSize=16, alignment=TA_CENTER, spaceAfter=6,
            textColor=colors.HexColor(primary_color),

        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            fontName=fn,
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=4,
            textColor=colors.HexColor("#555555"),
        ),
        "meta_key": ParagraphStyle(
            "MetaKey", fontName=fnb, fontSize=9, alignment=TA_RIGHT
        ),
        "meta_val": ParagraphStyle(
            "MetaVal", fontName=fn, fontSize=9, alignment=TA_RIGHT
        ),
        "table_header": ParagraphStyle(
            "TH", fontName=fnb, fontSize=8, alignment=TA_CENTER
        ),
        "table_cell": ParagraphStyle(
            "TC", fontName=fn, fontSize=8, alignment=TA_CENTER
        ),
        "signature": ParagraphStyle(
            "Sig", fontName=fn, fontSize=10, alignment=TA_CENTER, spaceBefore=20
        ),
        "footer": ParagraphStyle(
            "Footer",
            fontName=fn,
            fontSize=7,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#999999"),
        ),
    }
    if compact:
        for style in styles.values():
            style.fontSize = max(6, style.fontSize - 1)
            style.leading = max(style.fontSize + 1, style.leading - 1)
    return styles


def _generate_receipt_pdf_single(
    receipt_no,
    institution,
    tx_type,
    date_text,
    sender_name="",
    receiver_name="",
    sender_org="",
    receiver_org="",
    items=None,
    notes="",
    transport_info="",
    authorization_no="",
    authorization_date="",
    additional_comments="",
    status_text="",
    transaction_time="",
    created_at_text="",
    updated_at_text="",
    logo_path=None,
    copy_label="",
    paper_size=A4,
    output_path=None,
    company_name=None,
    subtitle=None,
    footer_text=None,
    primary_color="#1D4E89",
):
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
        authorization_no: Optional authorization/reference number
        authorization_date: Optional authorization date
        additional_comments: Optional extra comments
        status_text: Optional localized receipt status
        transaction_time: Optional transaction time
        created_at_text: Optional detailed creation timestamp
        updated_at_text: Optional detailed update timestamp
        copy_label: Optional recipient/sender copy label
        paper_size: ReportLab page size, such as A4 or A5

    Returns:
        Path to the generated PDF file
    """
    pdf_path = Path(output_path) if output_path else STORAGE_DIR / "receipts" / f"{receipt_no}.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    transaction_time = format_receipt_datetime(transaction_time)
    created_at_text = format_receipt_datetime(created_at_text)
    updated_at_text = format_receipt_datetime(updated_at_text)
    company_name = company_name or os.environ.get("LAB_RECEIPT_COMPANY_NAME", "نظام إدارة الاستلام المختبري")
    subtitle = subtitle or os.environ.get("LAB_RECEIPT_SUBTITLE", "إيصال رسمي")
    footer_text = footer_text or os.environ.get("LAB_RECEIPT_FOOTER", "")
    logo_path = logo_path or _default_logo_path()

    compact = paper_size == A5
    margin = 8 if compact else 15
    top_margin = 10 if compact else 20
    bottom_margin = 8 if compact else 15
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=paper_size,
        rightMargin=margin * mm,
        leftMargin=margin * mm,
        topMargin=top_margin * mm,
        bottomMargin=bottom_margin * mm,
        encoding="utf-8",
    )

    s = _styles(primary_color, compact=compact)
    elements = []

    # ---- Header ----
    elements.append(Paragraph(_display_text(company_name), s["title"]))
    elements.append(Paragraph(_display_text(subtitle), s["subtitle"]))
    if copy_label:
        elements.append(Paragraph(_display_text(copy_label), s["subtitle"]))
    elements.append(Spacer(1, (3 if compact else 6) * mm))

    # ---- Logo (if provided) ----
    if logo_path and Path(logo_path).exists():
        try:
            img = RLImage(str(logo_path), width=3 * cm, height=3 * cm)
            elements.append(img)
        except Exception:
            pass

    # ---- Meta information table ----
    meta_data = [
        [Paragraph(_display_text("رقم الإيصال"), s["meta_key"]), Paragraph(_display_text(receipt_no), s["meta_val"])],
        [Paragraph(_display_text("نوع المعاملة"), s["meta_key"]), Paragraph(_display_text(tx_type), s["meta_val"])],
        [Paragraph(_display_text("الجهة"), s["meta_key"]), Paragraph(_display_text(institution), s["meta_val"])],
        [Paragraph(_display_text("التاريخ"), s["meta_key"]), Paragraph(_display_text(date_text), s["meta_val"])],
    ]
    if sender_org:
        meta_data.append(
            [
                Paragraph(_display_text("الجهة المرسلة"), s["meta_key"]),
                Paragraph(_display_text(sender_org), s["meta_val"]),
            ]
        )
    if receiver_org:
        meta_data.append(
            [
                Paragraph(_display_text("الجهة المستقبلة"), s["meta_key"]),
                Paragraph(_display_text(receiver_org), s["meta_val"]),
            ]
        )
    if sender_name:
        meta_data.append(
            [Paragraph(_display_text("المرسل"), s["meta_key"]), Paragraph(_display_text(sender_name), s["meta_val"])]
        )
    if receiver_name:
        meta_data.append(
            [
                Paragraph(_display_text("المستلم"), s["meta_key"]),
                Paragraph(_display_text(receiver_name), s["meta_val"]),
            ]
        )
    if authorization_no:
        meta_data.append(
            [
                Paragraph(_display_text("رقم التفويض"), s["meta_key"]),
                Paragraph(_display_text(authorization_no), s["meta_val"]),
            ]
        )
    if authorization_date:
        meta_data.append(
            [
                Paragraph(_display_text("تاريخ التفويض"), s["meta_key"]),
                Paragraph(_display_text(authorization_date), s["meta_val"]),
            ]
        )
    if status_text:
        meta_data.append(
            [
                Paragraph(_display_text("الحالة"), s["meta_key"]),
                Paragraph(_display_text(status_text), s["meta_val"]),
            ]
        )
    if transaction_time:
        meta_data.append(
            [
                Paragraph(_display_text("وقت المعاملة"), s["meta_key"]),
                Paragraph(_display_text(transaction_time), s["meta_val"]),
            ]
        )
    if created_at_text:
        meta_data.append(
            [
                Paragraph(_display_text("تاريخ ووقت التسجيل"), s["meta_key"]),
                Paragraph(_display_text(created_at_text), s["meta_val"]),
            ]
        )
    if updated_at_text:
        meta_data.append(
            [
                Paragraph(_display_text("آخر تحديث"), s["meta_key"]),
                Paragraph(_display_text(updated_at_text), s["meta_val"]),
            ]
        )

    meta_table = Table(meta_data, colWidths=[doc.width * 0.3, doc.width * 0.7])
    meta_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#EEEEEE")),
            ]
        )
    )
    elements.append(meta_table)
    elements.append(Spacer(1, (3 if compact else 6) * mm))

    # ---- Items table ----
    if items and len(items) > 0:
        elements.append(Paragraph("العينات", s["subtitle"]))
        elements.append(Spacer(1, 2 * mm))

        header = [
            "نوع العينة",
            "المجموع",
            "صالح",
            "تالف",
            "مرفوض",
            "غير مطابق",
            "حالة النقل",
        ]
        table_data = [[Paragraph(_display_text(h), s["table_header"]) for h in header]]

        for item in items:
            row = [
                Paragraph(_display_text(item.get("sample_name", "")), s["table_cell"]),
                Paragraph(str(item.get("total_count", 0)), s["table_cell"]),
                Paragraph(str(item.get("valid_count", 0)), s["table_cell"]),
                Paragraph(str(item.get("damaged_count", 0)), s["table_cell"]),
                Paragraph(str(item.get("rejected_count", 0)), s["table_cell"]),
                Paragraph(str(item.get("non_conforming_count", 0)), s["table_cell"]),
                Paragraph(_display_text(item.get("transport_condition", "")), s["table_cell"]),
            ]
            table_data.append(row)

        # Totals row
        total_row = ["الإجمالي"]
        for key in [
            "total_count",
            "valid_count",
            "damaged_count",
            "rejected_count",
            "non_conforming_count",
        ]:
            total_row.append(str(sum(int(it.get(key, 0)) for it in items)))
        total_row.append("")
        table_data.append([Paragraph(c, s["table_header"]) for c in total_row])

        col_widths = [
            doc.width * 0.18,
            doc.width * 0.10,
            doc.width * 0.10,
            doc.width * 0.10,
            doc.width * 0.10,
            doc.width * 0.12,
            doc.width * 0.20,
        ]
        item_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        item_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(_safe_hex_color(primary_color))),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8F0FE")),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -2),
                        [colors.white, colors.HexColor("#F8FAFC")],
                    ),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(item_table)
        elements.append(Spacer(1, (2 if compact else 4) * mm))

    # ---- Notes & transport ----
    if notes:
        elements.append(Paragraph(f"<b>{_display_text('ملاحظات:')}</b> {_display_text(notes)}", s["meta_val"]))
    if transport_info:
        elements.append(
            Paragraph(f"<b>{_display_text('معلومات النقل:')}</b> {_display_text(transport_info)}", s["meta_val"])
        )
    if additional_comments:
        elements.append(
            Paragraph(f"<b>{_display_text('تعليقات إضافية:')}</b> {_display_text(additional_comments)}", s["meta_val"])
        )

    elements.append(Spacer(1, (4 if compact else 10) * mm))

    # ---- QR Code ----
    temp_files = []
    try:
        qr_data = f"{receipt_no}|{institution}|{date_text}|{tx_type}"
        qr_img = qrcode.make(qr_data)

        qr_tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        qr_tmp.close()
        qr_path = Path(qr_tmp.name)
        qr_img.save(str(qr_path))
        temp_files.append(qr_path)
        qr_size = 2 * cm if compact else 3 * cm
        qr_rl = RLImage(str(qr_path), width=qr_size, height=qr_size)
        elements.append(qr_rl)
    except Exception:
        pass

    # ---- Barcode ----
    try:

        bar_tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        bar_tmp.close()
        bar_path = Path(bar_tmp.name)
        with open(str(bar_path), "wb") as f:
            Code128(receipt_no, writer=ImageWriter()).write(f)
        temp_files.append(bar_path)
        bar_rl = RLImage(str(bar_path), width=(6 if compact else 8) * cm, height=(1 if compact else 1.5) * cm)
        elements.append(Spacer(1, 2 * mm))
        elements.append(bar_rl)
    except Exception:
        pass

    elements.append(Spacer(1, (4 if compact else 10) * mm))

    # ---- Signature section ----
    sig_table = Table(
        [
            [
                Paragraph(_display_text("توقيع المرسل: _____________"), s["signature"]),
                Paragraph(_display_text("توقيع المستلم: _____________"), s["signature"]),
            ]
        ],
        colWidths=[doc.width * 0.5, doc.width * 0.5],
    )
    sig_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(sig_table)

    # ---- Footer ----
    elements.append(Spacer(1, (3 if compact else 8) * mm))
    elements.append(
        Paragraph(
            _display_text(footer_text or f"نظام إدارة الاستلام المختبري — الإصدار {CONFIG.app_version} — {datetime.now().year}"),
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


def _merge_a5_copies_on_a4(first_path, second_path, output_path):
    """Place two one-page A5 PDFs side by side on one landscape A4 page."""
    from pypdf import Transformation

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    first = PdfReader(str(first_path)).pages
    second = PdfReader(str(second_path)).pages
    page_count = max(len(first), len(second))
    a4_width, a4_height = landscape(A4)
    for page_index in range(page_count):
        base = writer.add_blank_page(width=a4_width, height=a4_height)
        for copy_index, source_pages in enumerate((first, second)):
            if page_index >= len(source_pages):
                continue
            page = source_pages[page_index]
            source_width = float(page.mediabox.width)
            source_height = float(page.mediabox.height)
            scale_x = A5[0] / source_width if source_width else 1
            scale_y = A5[1] / source_height if source_height else 1
            transform = Transformation().scale(sx=scale_x, sy=scale_y).translate(
                tx=copy_index * A5[0], ty=0
            )
            base.merge_transformed_page(page, transform, over=True)
    with output_path.open("wb") as stream:
        writer.write(stream)
    return output_path


def generate_receipt_pdf(*args, print_format="a4", **kwargs):
    """Generate a receipt in A4, A5, or two A5 copies on one A4 sheet."""
    normalized = str(print_format or "a4").lower().replace("_", "-")
    if normalized not in {"a4", "a5", "a4-two-up", "two-up", "a4-2up"}:
        raise ValueError("تنسيق الطباعة غير مدعوم. استخدم a4 أو a5 أو a4-two-up")
    receipt_no = str(kwargs.get("receipt_no") or (args[0] if args else "receipt"))
    if normalized == "a5":
        kwargs["paper_size"] = A5
        return _generate_receipt_pdf_single(*args, **kwargs)
    if normalized == "a4":
        kwargs["paper_size"] = A4
        return _generate_receipt_pdf_single(*args, **kwargs)

    base_dir = Path(kwargs.pop("output_path", STORAGE_DIR / "receipts"))
    if base_dir.suffix.lower() == ".pdf":
        output_path = base_dir
    else:
        output_path = base_dir / f"{receipt_no}_two_up.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="receipt-two-up-", dir=str(output_path.parent)) as temp_dir:
        first_path = Path(temp_dir) / f"{receipt_no}_recipient_a5.pdf"
        second_path = Path(temp_dir) / f"{receipt_no}_sender_a5.pdf"
        first_kwargs = dict(kwargs, output_path=first_path, paper_size=A5, copy_label="نسخة المستلم")
        second_kwargs = dict(kwargs, output_path=second_path, paper_size=A5, copy_label="نسخة المرسل")
        _generate_receipt_pdf_single(*args, **first_kwargs)
        _generate_receipt_pdf_single(*args, **second_kwargs)
        _merge_a5_copies_on_a4(first_path, second_path, output_path)
    return output_path
