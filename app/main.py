import os
from re import T
from fastapi import FastAPI, WebSocket

from contextlib import asynccontextmanager
import asyncio

from starlette.websockets import WebSocketState, WebSocketDisconnect

import signal

from app.api.rest import *
from app.api.websocket import create_broker_ws
from app.utils.process import signal_handler
from app.global_vars import get_broker_ws, get_cred

from app.routers import rest, websocket

import firebase_admin

from app.utils.websocket import broadcast_data
import app.utils.websocket

def write_service_account_file(file_path: str = "./service-account.json"):
    json_str = os.getenv("SERVICE_ACCOUNT_JSON")
    if not json_str:
        raise RuntimeError("SERVICE_ACCOUNT_JSON environment variable is not set")

    with open(file_path, "w") as f:
        f.write(json_str)

firebase_admin.initialize_app(get_cred())

@asynccontextmanager
async def lifespan(app: FastAPI):
    fetch_task = None
    broadcast_task = None

    async def startup():
        nonlocal fetch_task, broadcast_task
        broker_ws = get_broker_ws()

        fetch_task = asyncio.create_task(broker_ws.ws_client())
        await asyncio.sleep(1)
        broadcast_task = asyncio.create_task(broadcast_data())

        print("서버 시작: 실시간 WebSocket 감시 시작")
    
    async def shutdown():
        print("서버 종료. WebSocket 연결을 종료합니다.")
        broker_ws = get_broker_ws()
        nonlocal fetch_task, broadcast_task
        if broker_ws is not None:
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
