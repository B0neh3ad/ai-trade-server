from fastapi import APIRouter, WebSocket
from app.api import websocket_handler

router = APIRouter()

@router.websocket("/H0STASP0")
async def websocket_orderbook(websocket: WebSocket):
    await websocket_handler(
        websocket,
        tr_id_list=["H0STASP0"],
        tr_key_list=["005930"]
    )

@router.websocket("/H0STCNT0")
async def websocket_execution(websocket: WebSocket):
    await websocket_handler(
        websocket,
        tr_id_list=["H0STCNT0"],
        tr_key_list=["005930"]
    )