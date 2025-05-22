from fastapi import FastAPI, WebSocket

from contextlib import asynccontextmanager
import asyncio
import threading

from starlette.websockets import WebSocketState, WebSocketDisconnect

import signal

from app.api.rest import *
from app.utils.process import signal_handler
from app.utils.websocket import listen_price
from app.global_vars import global_broker_ws, cred

from app.routers import rest, websocket

from firebase_admin import credentials, firestore
import firebase_admin

# 서비스 계정 키 JSON 경로
cred = credentials.Certificate("./service-account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# 주가 감시 설정
NOTIFICATION_EXPIRY_TIME = 30 * 60  # 30분 (초 단위)
TARGET_PRICES = list(range(340, 350, 1))

def start_listen_price():
    asyncio.run(listen_price())

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: realtime_ws 시작
    lp_thread = threading.Thread(target=start_listen_price, daemon=True)
    lp_thread.start()
    print("서버 시작: 실시간 WebSocket 감시 시작")
    
    yield
    
    # shutdown: 모든 websocket 연결 종료
    print("서버 종료. WebSocket 연결을 종료합니다.")
    if global_broker_ws is not None:
        try:
            await global_broker_ws.websocket.close()
        except Exception as e:
            print(f"웹소켓 종료 중 에러: {e}")

    # 종료를 위해 스레드 종료 대기 (필요에 따라 join 시간 조정)
    lp_thread.join(timeout=5)

# app = FastAPI()
app = FastAPI(lifespan=lifespan)

app.include_router(rest.router)
app.include_router(websocket.router)

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)
