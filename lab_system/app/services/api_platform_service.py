"""
API Platform Service — API v1 Readiness

Provides API contract management, versioning, endpoint registration,
and standardized response formatting.
"""

from datetime import datetime
from typing import Any


class APIPlatform:
    """API platform management and versioning."""

    def __init__(self):
        self._endpoints: list[dict] = []
        self._versions = ["v1"]
        self._v1_contract = {
            "version": "v1",
            "title": "LabReceiptSystem API",
            "description": "Laboratory Receipt and Delivery Management API",
            "endpoints": {
                "receipts": {
                    "list": "GET /api/v1/receipts",
                    "get": "GET /api/v1/receipts/{id}",
                    "create": "POST /api/v1/receipts",
                    "update": "PUT /api/v1/receipts/{id}",
                    "delete": "DELETE /api/v1/receipts/{id}",
                },
                "organizations": {
                    "list": "GET /api/v1/organizations",
                    "get": "GET /api/v1/organizations/{id}",
                    "create": "POST /api/v1/organizations",
                },
                "users": {
                    "list": "GET /api/v1/users",
                    "get": "GET /api/v1/users/{id}",
                    "create": "POST /api/v1/users",
                },
                "health": {
                    "check": "GET /api/v1/health",
                },
            },
        }

    def get_v1_contract(self) -> dict:
        """Get API v1 contract."""
        return self._v1_contract

    def get_supported_versions(self) -> list[str]:
        """Get list of supported API versions."""
        return self._versions.copy()

    def register_endpoint(self, method: str, path: str, handler: str) -> dict:
        """Register an API endpoint."""
        endpoint = {
            "method": method,
            "path": path,
            "handler": handler,
            "registered_at": datetime.now().isoformat(timespec="seconds"),
        }
        self._endpoints.append(endpoint)
        return endpoint

    def get_endpoints(self) -> list[dict]:
        """Get all registered endpoints."""
        return self._endpoints.copy()

    def format_response(self, status_code: int, data: Any, message: str = "OK") -> dict:
        """Format a standardized API response."""
        return {
            "status_code": status_code,
            "data": data,
            "message": message,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def format_error(self, status_code: int, error: str, details: Any = None) -> dict:
        """Format a standardized API error response."""
        response = {
            "status_code": status_code,
            "error": error,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        if details:
            response["details"] = details
        return response

    def validate_request(self, method: str, path: str) -> dict:
        """Validate an API request against registered endpoints."""
        for ep in self._endpoints:
            if ep["method"] == method and ep["path"] == path:
                return {"valid": True, "endpoint": ep}
        return {"valid": False, "error": f"No endpoint found for {method} {path}"}
