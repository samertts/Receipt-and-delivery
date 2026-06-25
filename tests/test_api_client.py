"""API client tests."""

import json
import os
import sys
from unittest.mock import MagicMock, patch
import urllib.error


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestAPIClientInit:
    def test_default_init(self):
        from lab_system.app.sync.api_client import APIClient
        client = APIClient()
        assert client.is_enabled is False
        assert client.base_url == ""

    def test_custom_init(self):
        from lab_system.app.sync.api_client import APIClient
        client = APIClient(base_url="https://api.example.com", timeout=60)
        assert client.base_url == "https://api.example.com"
        assert client.timeout == 60


class TestAPIClientEnableDisable:
    def test_enable(self):
        from lab_system.app.sync.api_client import APIClient
        client = APIClient()
        client.enable("https://api.example.com", token="abc123")
        assert client.is_enabled is True
        assert client.base_url == "https://api.example.com"
        assert client._token == "abc123"

    def test_disable(self):
        from lab_system.app.sync.api_client import APIClient
        client = APIClient()
        client.enable("https://api.example.com")
        client.disable()
        assert client.is_enabled is False
        assert client._token == ""

    def test_set_token(self):
        from lab_system.app.sync.api_client import APIClient
        client = APIClient()
        client.set_token("mytoken")
        assert client._token == "mytoken"


class TestAPIClientPush:
    def test_push_disabled(self):
        from lab_system.app.sync.api_client import APIClient, SyncPayload
        client = APIClient()
        payload = SyncPayload(entries=[{"test": True}], device_id="d1", branch_id="b1")
        result = client.push(payload)
        assert result.success is False
        assert "disabled" in result.message.lower()

    @patch("urllib.request.urlopen")
    def test_push_enabled_success(self, mock_urlopen):
        from lab_system.app.sync.api_client import APIClient, SyncPayload
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"status": "ok"}).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        mock_urlopen.return_value = mock_resp

        client = APIClient()
        client.enable("https://api.example.com", token="test-token")
        payload = SyncPayload(entries=[{"test": True}], device_id="d1", branch_id="b1")
        result = client.push(payload)
        assert result.success is True
        assert result.status_code == 200


class TestAPIClientPull:
    def test_pull_disabled(self):
        from lab_system.app.sync.api_client import APIClient
        client = APIClient()
        result = client.pull(since="2026-01-01", device_id="d1")
        assert result.success is False


class TestAPIClientStatus:
    def test_status_disabled(self):
        from lab_system.app.sync.api_client import APIClient
        client = APIClient()
        result = client.status()
        assert result.success is False


class TestAPIClientSend:
    @patch("urllib.request.urlopen")
    def test_send_connection_error(self, mock_urlopen):
        from lab_system.app.sync.api_client import APIClient
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        client = APIClient()
        client.enable("https://api.example.com")
        result = client._send("GET", "/test", None)
        assert result.success is False
        assert result.status_code == 0

    @patch("urllib.request.urlopen")
    def test_send_http_error(self, mock_urlopen):
        from lab_system.app.sync.api_client import APIClient
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"detail": "Not found"}).encode()
        error = urllib.error.HTTPError(
            url="https://api.example.com/test",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=mock_resp,
        )
        mock_urlopen.side_effect = error

        client = APIClient()
        client.enable("https://api.example.com")
        result = client._send("GET", "/test", None)
        assert result.success is False
        assert result.status_code == 404
        assert result.data.get("detail") == "Not found"

    @patch("urllib.request.urlopen")
    def test_send_success_with_body(self, mock_urlopen):
        from lab_system.app.sync.api_client import APIClient
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"key": "value"}).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        mock_urlopen.return_value = mock_resp

        client = APIClient()
        client.enable("https://api.example.com")
        result = client._send("POST", "/test", {"data": "test"})
        assert result.success is True
        assert result.data == {"key": "value"}

    @patch("urllib.request.urlopen")
    def test_send_success_empty_body(self, mock_urlopen):
        from lab_system.app.sync.api_client import APIClient
        mock_resp = MagicMock()
        mock_resp.read.return_value = b""
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        mock_urlopen.return_value = mock_resp

        client = APIClient()
        client.enable("https://api.example.com")
        result = client._send("GET", "/test", None)
        assert result.success is True


class TestSyncPayload:
    def test_default_payload(self):
        from lab_system.app.sync.api_client import SyncPayload
        p = SyncPayload()
        assert p.entries == []
        assert p.device_id == ""
        assert p.branch_id == ""

    def test_custom_payload(self):
        from lab_system.app.sync.api_client import SyncPayload
        p = SyncPayload(entries=[{"a": 1}], device_id="d1", branch_id="b1")
        assert len(p.entries) == 1
        assert p.device_id == "d1"
