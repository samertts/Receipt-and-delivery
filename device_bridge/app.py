"""Optional localhost-only bridge for OS printers.

The browser-first UI does not require this process. This bridge only adds
best-effort CUPS text printing when the user explicitly runs it locally.
"""
from __future__ import annotations

import hmac
import os
import re
import shutil
import subprocess
import tempfile
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

TOKEN_HEADER = "X-Device-Bridge-Token"
PRINTER_NAME = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def configured_token() -> str:
    return os.getenv("DEVICE_BRIDGE_TOKEN", "").strip()


def allowed_origins() -> list[str]:
    raw = os.getenv("BRIDGE_ALLOWED_ORIGINS", DEFAULT_ORIGINS)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(title="Receipt and Delivery Device Bridge", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", TOKEN_HEADER],
)


class PrintRequest(BaseModel):
    content: str = Field(min_length=1, max_length=200_000)
    printer: str | None = Field(default=None, max_length=128)
    content_type: Literal["text"] = "text"


def require_token(token: str | None = Header(default=None, alias=TOKEN_HEADER)) -> None:
    expected = configured_token()
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Bridge token is not configured")
    if not token or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bridge token")


def cups_available() -> bool:
    return shutil.which("lpstat") is not None and shutil.which("lp") is not None


def list_cups_printers() -> list[str]:
    if not cups_available():
        return []
    result = subprocess.run(
        ["lpstat", "-p"],
        capture_output=True,
        text=True,
        timeout=3,
        check=False,
    )
    printers: list[str] = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "printer" and PRINTER_NAME.fullmatch(parts[1]):
            printers.append(parts[1])
    return printers


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "backend": "cups" if cups_available() else None, "printer_support": cups_available()}


@app.get("/printers", dependencies=[Depends(require_token)])
def printers() -> dict[str, object]:
    return {"printers": [{"name": name} for name in list_cups_printers()], "backend": "cups" if cups_available() else None}


@app.post("/print", dependencies=[Depends(require_token)])
def print_text(request: PrintRequest) -> dict[str, object]:
    if request.printer and not PRINTER_NAME.fullmatch(request.printer):
        raise HTTPException(status_code=400, detail="Invalid printer name")
    if not cups_available():
        raise HTTPException(status_code=501, detail="CUPS printing is not available on this computer")

    path = ""
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".txt", delete=False) as handle:
            handle.write(request.content)
            path = handle.name
        command = ["lp"]
        if request.printer:
            command.extend(["-d", request.printer])
        command.append(path)
        result = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
        if result.returncode != 0:
            raise HTTPException(status_code=502, detail="The operating system printer rejected the job")
        return {"queued": True, "printer": request.printer, "message": result.stdout.strip() or "Print job queued"}
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="The printer timed out") from exc
    finally:
        if path:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.getenv("BRIDGE_HOST", "127.0.0.1"),
        port=int(os.getenv("BRIDGE_PORT", "17321")),
        reload=False,
    )
