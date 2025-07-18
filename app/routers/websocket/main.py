from fastapi import APIRouter, WebSocket
from app.services.websocket import manage_subscription

router = APIRouter()
            
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await manage_subscription(websocket)
