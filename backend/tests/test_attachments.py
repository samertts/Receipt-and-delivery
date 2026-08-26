from app.api.v1 import attachments


def _unwrap(body):
    return body.get("data", body)


def _create_transaction(client, admin_token):
    response = client.post(
        "/api/transactions",
        json={
            "transaction_type": "Sample Receipt",
            "sender_organization_id": "00000000-0000-0000-0000-000000000001",
            "receiver_organization_id": "00000000-0000-0000-0000-000000000002",
            "sender_name": "Sender",
            "receiver_name": "Receiver",
            "transaction_date": "2026-08-26",
            "status": "draft",
            "items": [{
                "sample_type": "Serum",
                "total_count": 1,
                "valid_count": 1,
                "damaged_count": 0,
                "rejected_count": 0,
                "nonconforming_count": 0,
                "transport_condition": "Good",
            }],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    return _unwrap(response.json())["id"]


def test_upload_and_download_attachment_uses_validated_private_path(client, admin_token, tmp_path, monkeypatch):
    monkeypatch.setattr(attachments, "UPLOAD_DIR", tmp_path / "attachments")
    transaction_id = _create_transaction(client, admin_token)
    content = b"%PDF-1.7\nsecure test"

    upload = client.post(
        "/api/attachments/upload",
        params={"transaction_id": transaction_id},
        files={"file": ("report.pdf", content, "application/pdf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert upload.status_code == 200
    attachment_id = _unwrap(upload.json())["id"]
    downloaded = client.get(
        f"/api/attachments/{attachment_id}/download",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert downloaded.status_code == 200
    assert downloaded.content == content
    assert list((tmp_path / "attachments").glob("*.pdf"))


def test_upload_rejects_oversized_content_without_leaving_file(client, admin_token, tmp_path, monkeypatch):
    monkeypatch.setattr(attachments, "UPLOAD_DIR", tmp_path / "attachments")
    monkeypatch.setattr(attachments, "MAX_FILE_SIZE", 8)
    transaction_id = _create_transaction(client, admin_token)

    response = client.post(
        "/api/attachments/upload",
        params={"transaction_id": transaction_id},
        files={"file": ("large.pdf", b"%PDF-1.7\nX", "application/pdf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400
    assert not list((tmp_path / "attachments").glob("*"))
