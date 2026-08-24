from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.blacklisted_token import BlacklistedToken
from app.models.user import User
from app.services.notification_service import notification_manager
from app.services.security import decode_access_token

router = APIRouter(prefix="/ws", tags=["التنبيهات الفورية"])


@router.websocket("/notifications")
async def notifications_socket(
    websocket: WebSocket,
    db: Session = Depends(get_db),
) -> None:
    token = websocket.query_params.get("token", "")
    user_id = ""

    try:
        payload = decode_access_token(token)
        if not payload:
            await websocket.close(code=1008, reason="رمز مصادقة غير صالح")
            return

        if db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first():
            await websocket.close(code=1008, reason="تم إبطال الرمز")
            return

        user = db.query(User).filter(User.username == payload["sub"]).first()
        if not user or user.status != "active":
            await websocket.close(code=1008, reason="الحساب غير نشط")
            return

        user_id = str(user.id)
        await notification_manager.connect(user_id, websocket)
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
