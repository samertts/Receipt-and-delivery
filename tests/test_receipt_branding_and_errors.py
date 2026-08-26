import pytest

from lab_system.app.services.receipt_branding_service import ReceiptBrandingService
from lab_system.app.utils.errors import ValidationError, to_arabic_error


def test_receipt_branding_round_trip_is_atomic_and_validated(tmp_path):
    settings_path = tmp_path / "settings" / "receipt_branding.json"
    service = ReceiptBrandingService(settings_path)
    saved = service.save(
        {
            "company_name": "مختبر الأمان",
            "subtitle": "إيصال استلام",
            "primary_color": "#ab12ef",
            "layout": "a5",
        }
    )

    assert saved["company_name"] == "مختبر الأمان"
    assert saved["primary_color"] == "#AB12EF"
    assert service.load()["layout"] == "a5"
    assert settings_path.is_file()


def test_receipt_branding_rejects_untrusted_logo_and_layout(tmp_path):
    service = ReceiptBrandingService(tmp_path / "branding.json")
    with pytest.raises(ValidationError):
        service.save({"logo_path": str(tmp_path / "logo.svg")})
    with pytest.raises(ValidationError):
        service.save({"layout": "thermal"})


def test_arabic_error_messages_do_not_expose_raw_exception():
    raw = "Permission denied: /secret/laboratory/database.db"
    message = to_arabic_error(PermissionError(raw), "حفظ الإيصال")

    assert "لا يمكن الوصول" in message
    assert "/secret" not in message
    assert raw not in message
