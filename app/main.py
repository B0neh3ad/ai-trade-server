from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
import signal

from app.global_vars import get_broker_ws, get_cred
from app.routers import rest, websocket
import firebase_admin
from app.services.websocket import broadcast_data, update_option_subscriptions
from app.db.background_tasks import get_background_tasks

firebase_admin.initialize_app(get_cred())

@asynccontextmanager
async def lifespan(app: FastAPI):
    fetch_task = None
    broadcast_task = None
    option_task = None
    background_tasks = get_background_tasks()

    async def startup():
        nonlocal fetch_task, broadcast_task, option_task
        broker_ws = get_broker_ws()

        fetch_task = asyncio.create_task(broker_ws.ws_client())
        await asyncio.sleep(1)
        
        broadcast_task = asyncio.create_task(broadcast_data())
        await asyncio.sleep(1)
        
        option_task = asyncio.create_task(update_option_subscriptions())
        
        # Start background tasks for database maintenance
        await background_tasks.start()

        print("서버 시작: 실시간 WebSocket 감시 시작")
    
    async def shutdown():
        print("서버 종료. WebSocket 연결을 종료합니다.")
        
        # Stop background tasks first
        await background_tasks.stop()
        
        broker_ws = get_broker_ws()
        nonlocal fetch_task, broadcast_task, option_task
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
        if option_task:
            option_task.cancel()
            try:
                await option_task
            except asyncio.CancelledError:
                print(f"option_task 종료 완료")

    
    await startup()
    yield
    await shutdown()

def signal_handler(sig, frame):
    # TODO: 구독 중이던 정보 전부 구독 취소하기
    print("\n🛑 Keyboard interrupt received.")

# app = FastAPI()
app = FastAPI(lifespan=lifespan)

app.include_router(rest.router)
app.include_router(websocket.router)

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)
