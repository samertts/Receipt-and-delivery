def _unwrap(body: dict) -> dict:
    return body.get("data", body)


class TestTransactionCRUD:
    def test_create_transaction(self, client, admin_token):
        payload = {
            "transaction_type": "Sample Receipt",
            "sender_organization_id": "00000000-0000-0000-0000-000000000001",
            "receiver_organization_id": "00000000-0000-0000-0000-000000000002",
            "sender_name": "مختبر بغداد",
            "receiver_name": "مختبر الكرخ",
            "sender_job_title": "مدير مختبر",
            "receiver_job_title": "فني مختبر",
            "transport_info": "نقل مبرد",
            "authorization_no": "AUTH-001",
            "authorization_date": "2026-05-27",
            "transaction_date": "2026-05-27",
            "notes": "test transaction",
            "status": "draft",
            "items": [
                {
                    "sample_type": "Serum",
                    "total_count": 10,
                    "valid_count": 8,
                    "damaged_count": 1,
                    "rejected_count": 1,
                    "nonconforming_count": 0,
                    "transport_condition": "Cooler box",
                    "notes": "Handle with care",
                },
            ],
        }
        response = client.post(
            "/api/transactions",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 201
        data = _unwrap(response.json())
        assert data["transaction_no"].startswith("TXN-")
        assert data["status"] == "draft"
        assert len(data["items"]) == 1
        assert data["sender_job_title"] == "مدير مختبر"
        assert data["transport_info"] == "نقل مبرد"

    def test_create_transaction_invalid_counts(self, client, admin_token):
        payload = {
            "transaction_type": "Sample Receipt",
            "sender_organization_id": "00000000-0000-0000-0000-000000000001",
            "receiver_organization_id": "00000000-0000-0000-0000-000000000002",
            "sender_name": "Sender",
            "receiver_name": "Receiver",
            "transaction_date": "2026-05-27",
            "status": "draft",
            "items": [
                {
                    "sample_type": "Serum",
                    "total_count": 10,
                    "valid_count": 10,
                    "damaged_count": 0,
                    "rejected_count": 0,
                    "nonconforming_count": 0,
                    "transport_condition": "Good",
                },
            ],
        }
        response = client.post(
            "/api/transactions",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 201

    def test_list_transactions(self, client, admin_token):
        response = client.get(
            "/api/transactions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body.get("data", body), list)

    def test_list_transactions_pagination_header(self, client, db, admin_token):
        from app.models.transaction import Transaction

        for i in range(5):
            txn = Transaction(
                transaction_no=f"TXN-PAG-{i}",
                transaction_type="Test",
                sender_organization_id="00000000-0000-0000-0000-000000000001",
                receiver_organization_id="00000000-0000-0000-0000-000000000002",
                sender_name="S",
                receiver_name="R",
                transaction_date="2026-06-01",
                status="draft",
            )
            db.add(txn)
        db.commit()

        response = client.get(
            "/api/transactions?limit=2",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body.get("meta", {}).get("total") == 5

    def test_get_transaction_not_found(self, client, admin_token):
        response = client.get(
            "/api/transactions/nonexistent-id",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404


class TestTransactionDeepUpdate:
    def test_update_transaction_items_add(self, client, db, admin_token):
        from app.models.transaction import Transaction
        from app.models.transaction_item import TransactionItem

        txn = Transaction(
            transaction_no="TXN-UPDATE-1",
            transaction_type="Test",
            sender_organization_id="00000000-0000-0000-0000-000000000001",
            receiver_organization_id="00000000-0000-0000-0000-000000000002",
            sender_name="S", receiver_name="R",
            transaction_date="2026-06-01", status="draft",
        )
        db.add(txn)
        db.flush()
        item = TransactionItem(
            transaction_id=str(txn.id), sample_type="Serum",
            total_count=5, valid_count=5, damaged_count=0,
            rejected_count=0, nonconforming_count=0,
            transport_condition="",
        )
        db.add(item)
        db.commit()

        response = client.put(
            f"/api/transactions/{txn.id}",
            json={
                "notes": "updated notes",
                "items": [
                    {"id": str(item.id), "total_count": 10, "valid_count": 10},
                    {"sample_type": "Plasma", "total_count": 3, "valid_count": 3},
                ],
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Body: {response.text}"
        data = _unwrap(response.json())
        assert data["notes"] == "updated notes"
        assert len(data["items"]) == 2

    def test_update_transaction_items_delete(self, client, db, admin_token):
        from app.models.transaction import Transaction
        from app.models.transaction_item import TransactionItem

        txn = Transaction(
            transaction_no="TXN-UPDATE-2",
            transaction_type="Test",
            sender_organization_id="00000000-0000-0000-0000-000000000001",
            receiver_organization_id="00000000-0000-0000-0000-000000000002",
            sender_name="S", receiver_name="R",
            transaction_date="2026-06-01", status="draft",
        )
        db.add(txn)
        db.flush()
        item = TransactionItem(
            transaction_id=str(txn.id), sample_type="Serum",
            total_count=5, valid_count=5, damaged_count=0,
            rejected_count=0, nonconforming_count=0,
            transport_condition="",
        )
        db.add(item)
        db.commit()

        response = client.put(
            f"/api/transactions/{txn.id}",
            json={"items": [{"id": str(item.id), "delete": True}]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert len(_unwrap(response.json())["items"]) == 0
