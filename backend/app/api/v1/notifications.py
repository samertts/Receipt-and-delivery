from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.cookie_auth import ACCESS_COOKIE
from app.db.session import get_db
from app.models.blacklisted_token import BlacklistedToken
from app.models.user import User
from app.services.notification_service import notification_manager
from app.services.security import decode_access_token

router = APIRouter(prefix="/ws", tags=["التنبيهات الفورية"])


def _origin_is_allowed(websocket: WebSocket) -> bool:
    origin = websocket.headers.get("origin", "")
    return not origin or origin in settings.origin_list


def _find_user(token: str, db: Session) -> User | None:
    payload = decode_access_token(token)
    if not payload:
        return None
    if db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first():
        return None
    user = db.query(User).filter(User.username == payload.get("sub", "")).first()
    return user if user and user.status == "active" else None


@router.websocket("/notifications")
async def notifications_socket(
    websocket: WebSocket,
    db: Session = Depends(get_db),
) -> None:
    user_id = ""
    await websocket.accept()
    try:
        if not _origin_is_allowed(websocket):
            await websocket.close(code=1008, reason="مصدر الاتصال غير مسموح")
            return

        token = websocket.cookies.get(ACCESS_COOKIE, "")
        user = _find_user(token, db)
        if not user:
            await websocket.close(code=1008, reason="رمز مصادقة غير صالح")
            return

        user_id = str(user.id)
        connected = await notification_manager.connect(user_id, websocket, accepted=True)
        if not connected:
            await websocket.close(code=1013, reason="تم بلوغ حد الاتصالات")
            return
        await websocket.send_json(
            {
                "type": "connected",
                "message": "تم الاتصال بقناة التنبيهات الفورية",
            }
        )

        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        if user_id:
            await notification_manager.disconnect(user_id, websocket)
