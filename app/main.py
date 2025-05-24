from re import T
from fastapi import FastAPI, WebSocket

from contextlib import asynccontextmanager
import asyncio

from starlette.websockets import WebSocketState, WebSocketDisconnect

import signal

from app.api.rest import *
from app.api.websocket import create_broker_ws
from app.utils.process import signal_handler
from app.global_vars import cred

from app.routers import rest, websocket

from firebase_admin import credentials, firestore
import firebase_admin

from app.utils.websocket import broadcast_data

# 서비스 계정 키 JSON 경로
cred = credentials.Certificate("./service-account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# 주가 감시 설정
NOTIFICATION_EXPIRY_TIME = 30 * 60  # 30분 (초 단위)
TARGET_PRICES = list(range(340, 350, 1))

@asynccontextmanager
async def lifespan(app: FastAPI):
    fetch_task = None
    broadcast_task = None
    global_broker_ws = None

    async def startup():
        global global_broker_ws
        nonlocal fetch_task, broadcast_task
        global_broker_ws = create_broker_ws()

        fetch_task = asyncio.create_task(global_broker_ws.ws_client())
        await asyncio.sleep(1)

        broadcast_task = asyncio.create_task(broadcast_data(global_broker_ws))

        print("서버 시작: 실시간 WebSocket 감시 시작")
    
    async def shutdown():
        print("서버 종료. WebSocket 연결을 종료합니다.")
        global global_broker_ws
        nonlocal fetch_task, broadcast_task
        if global_broker_ws is not None:
            if fetch_task:
                fetch_task.cancel()
                try:
                    await fetch_task
                except asyncio.CancelledError:
                    print(f"fetch_task 종료 완료")
        if broadcast_task:
            broadcast_task.cancel()
            try:
                await broadcast_task
            except asyncio.CancelledError:
                print(f"broadcast_task 종료 완료")

    
    await startup()
    yield
    await shutdown()

# app = FastAPI()
app = FastAPI(lifespan=lifespan)

app.include_router(rest.router)
app.include_router(websocket.router)

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)
