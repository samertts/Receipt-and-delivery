from pathlib import Path

from lab_system.app.printing import receipt_pdf


def test_generate_receipt_pdf_contains_a_valid_pdf_and_accepts_full_receipt_data(tmp_path, monkeypatch):
    monkeypatch.setattr(receipt_pdf, "STORAGE_DIR", tmp_path)

    output = receipt_pdf.generate_receipt_pdf(
        receipt_no="LAB-2026-000001",
        institution="مختبر بغداد المركزي",
        tx_type="استلام عينات",
        date_text="2026-08-26",
        sender_name="أحمد علي",
        receiver_name="سارة حسن",
        sender_org="مركز صحي ألف",
        receiver_org="مختبر بغداد المركزي",
        items=[
            {
                "sample_name": "Serum",
                "total_count": 10,
                "valid_count": 9,
                "damaged_count": 1,
                "rejected_count": 0,
                "non_conforming_count": 0,
                "transport_condition": "جيدة",
            }
        ],
        notes="تم استلام العينات بحضور الطرفين.",
        transport_info="حافظة مبردة",
        authorization_no="AUTH-17",
        authorization_date="2026-08-25",
        additional_comments="يجب حفظ العينات وفق تعليمات المختبر.",
        status_text="معتمد",
    )

    assert output == Path(tmp_path) / "receipts" / "LAB-2026-000001.pdf"
    assert output.is_file()
    assert output.read_bytes().startswith(b"%PDF")
    assert output.stat().st_size > 1000
