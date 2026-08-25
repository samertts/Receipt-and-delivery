from fastapi.testclient import TestClient

from device_bridge import app as bridge


client = TestClient(bridge.app)


def test_health_does_not_expose_printers(monkeypatch):
    monkeypatch.delenv("DEVICE_BRIDGE_TOKEN", raising=False)
    response = client.get("/health")
    assert response.status_code == 200
    assert "printers" not in response.json()


def test_printers_requires_configured_token(monkeypatch):
    monkeypatch.setenv("DEVICE_BRIDGE_TOKEN", "test-secret")
    response = client.get("/printers")
    assert response.status_code == 401


def test_printers_accepts_valid_token(monkeypatch):
    monkeypatch.setenv("DEVICE_BRIDGE_TOKEN", "test-secret")
    monkeypatch.setattr(bridge, "list_cups_printers", lambda: ["lab_printer"])
    response = client.get("/printers", headers={bridge.TOKEN_HEADER: "test-secret"})
    assert response.status_code == 200
    assert response.json()["printers"] == [{"name": "lab_printer"}]


def test_print_rejects_untrusted_printer_name(monkeypatch):
    monkeypatch.setenv("DEVICE_BRIDGE_TOKEN", "test-secret")
    response = client.post(
        "/print",
        headers={bridge.TOKEN_HEADER: "test-secret"},
        json={"content": "test", "printer": "printer;rm -rf /"},
    )
    assert response.status_code == 400


def test_print_queues_text_without_shell(monkeypatch):
    monkeypatch.setenv("DEVICE_BRIDGE_TOKEN", "test-secret")
    monkeypatch.setattr(bridge, "cups_available", lambda: True)
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return type("Completed", (), {"returncode": 0, "stdout": "request id is 7"})()

    monkeypatch.setattr(bridge.subprocess, "run", fake_run)
    response = client.post(
        "/print",
        headers={bridge.TOKEN_HEADER: "test-secret"},
        json={"content": "Receipt test\n", "printer": "lab_printer"},
    )
    assert response.status_code == 200
    assert response.json()["queued"] is True
    assert calls[0][0][0] == "lp"
    assert calls[0][0][1:3] == ["-d", "lab_printer"]
    assert calls[0][1].get("shell", False) is not True
