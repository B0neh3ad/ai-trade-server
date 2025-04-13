from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
from starlette.websockets import WebSocketState
from fastapi.responses import JSONResponse

from api.api import fetch_stock_price, fetch_futureoption_price, create_broker_ws

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "KOSPI200 Futures API Server is running"}

@app.get("/price")
async def get_price():
    data = fetch_futureoption_price()
    return JSONResponse(content=data)

# WebSocket 연결
async def websocket_handler(
    websocket: WebSocket,
    tr_id_list: list[str],
    tr_key_list: list[str]
):
    await websocket.accept()

    try:
        init_msg = await asyncio.wait_for(websocket.receive_text(), timeout=5)
    except asyncio.TimeoutError:
        print("⏰ 클라이언트가 READY를 보내지 않아서 연결 종료")
        await websocket.close()
        return

    if init_msg != "READY":
        print(f"❗ 예상치 못한 초기 메시지: {init_msg}")
        await websocket.close()
        return

    print("✅ 클라이언트가 READY 상태입니다. 데이터 전송 시작")

    broker_ws = create_broker_ws(tr_id_list, tr_key_list)
    broker_ws.start()

    try:
        while True:
            data_ = broker_ws.get()
            data = data_[1]

            if websocket.application_state == WebSocketState.CONNECTED:
                try:
                    await asyncio.sleep(0.05)
                    await websocket.send_json(data)
                except Exception as e:
                    print(f"⚠️ 전송 에러 발생: {e}")
                    break
            else:
                print("⚠️ 웹소켓 연결 끊김")
                break
    except WebSocketDisconnect:
        print("🔌 클라이언트 연결 해제됨")
    except Exception as e:
        print(f"⚠️ 알 수 없는 에러: {e}")
    finally:
        if websocket.application_state != WebSocketState.DISCONNECTED:
            await websocket.close()
        print("🧹 WebSocket 세션 종료")

@app.websocket("/ws/hoga")
async def websocket_hoga(websocket: WebSocket):
    await websocket_handler(
        websocket,
        tr_id_list=["H0STASP0"],
        tr_key_list=["005930"]
    )

@app.websocket("/ws/price")
async def websocket_price(websocket: WebSocket):
    await websocket_handler(
        websocket,
        tr_id_list=["HOSTCNTO"],
        tr_key_list=["005930"]
    )
