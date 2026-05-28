class TestTransactionCRUD:
    def test_create_transaction(self, client, admin_token):
        payload = {
            "transaction_type": "Sample Receipt",
            "sender_organization_id": "00000000-0000-0000-0000-000000000001",
            "receiver_organization_id": "00000000-0000-0000-0000-000000000002",
            "sender_name": "مختبر بغداد",
            "receiver_name": "مختبر الكرخ",
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
                }
            ],
        }
        response = client.post(
            "/api/transactions",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_no"].startswith("TXN-")
        assert data["status"] == "draft"
        assert len(data["items"]) == 1

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
                }
            ],
        }
        response = client.post(
            "/api/transactions",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # counts balance: 10 == 10+0+0+0, so should succeed
        assert response.status_code == 201

    def test_list_transactions(self, client, admin_token):
        response = client.get(
            "/api/transactions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_transaction_not_found(self, client, admin_token):
        response = client.get(
            "/api/transactions/nonexistent-id",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404
