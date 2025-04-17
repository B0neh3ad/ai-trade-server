from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import JSONResponse

from multiprocessing import Process
from contextlib import asynccontextmanager
import asyncio
import threading

from pydantic import BaseModel
import requests
import httpx
import websockets
from starlette.websockets import WebSocketState, WebSocketDisconnect

import signal
import sys
import time

from api.api import *
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from utils import signal_handler
from global_vars import global_broker_ws, active_websockets

import google.auth
import google.auth.transport.requests
import firebase_admin
from firebase_admin import credentials, firestore

# 주가 감시 설정
NOTIFICATION_EXPIRY_TIME = 30 * 60  # 30분 (초 단위)
TARGET_PRICES = list(range(55000, 56000, 100))

# 서비스 계정 키 JSON 경로
cred = credentials.Certificate("./service-account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

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

################### REST API #####################

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

@app.get("/")
async def root():
    return {"message": "KOSPI200 Futures API Server is running"}

@app.get("/push")
async def push_notification():
    fcm_tokens = get_device_tokens()
    fcm_title = "Test"
    fcm_body = "test"

    print("디바이스 토큰 목록:", fcm_tokens)
    
    send_fcm_notification(
        tokens=fcm_tokens,
        title=fcm_title,
        body=fcm_body
    )
    
    return JSONResponse(content={"message": "Push notification sent"})

class FCMTokenData(BaseModel):
    userId: str
    token: str

@app.post("/fcmtoken")
async def store_fcm_token(data: FCMTokenData):
    try:
        # Firestore에 user_tokens 컬렉션에 저장 (userId를 document id로 사용)
        doc_ref = db.collection("user_tokens").document(data.userId)
        doc_ref.set({
            "token": data.token,
            "timestamp": firestore.SERVER_TIMESTAMP,
        })
        return {"message": "Token stored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/price")
async def get_price(symbol: str = "005930"):
    data = fetch_domestic_stock_price(symbol)
    return JSONResponse(content=data)

@app.get("/domestic-stock/price")
async def get_domestic_stock_price(symbol: str = "005930"):
    data = fetch_domestic_stock_price(symbol)
    return JSONResponse(content=data)

@app.get("/domestic-futureoption/price")
async def get_domestic_futureoption_price(market_code: str = "F", symbol: str = "101S03"):
    data = fetch_domestic_futureoption_price(market_code, symbol)
    return JSONResponse(content=data)

@app.get("/overseas-stock/price")
async def get_overseas_stock_price(symbol: str = "AAPL"):
    data = fetch_overseas_stock_price(symbol)
    return JSONResponse(content=data)

################### Websocket 데이터 전송 #####################

# Client와 handshake 수행
async def perform_client_handshake(websocket: WebSocket) -> bool:
    await websocket.accept()
    try:
        init_msg = await asyncio.wait_for(websocket.receive_text(), timeout=5)
    except asyncio.TimeoutError:
        print("⏰ 클라이언트가 READY를 보내지 않아서 연결 종료")
        await websocket.close()
        return False
    except WebSocketDisconnect:
        print("💨 클라이언트가 핸드셰이크 중에 연결 종료됨")
        return False

    if init_msg != "READY":
        print(f"❗ 예상치 못한 초기 메시지: {init_msg}")
        await websocket.close()
        return False

    print("✅ 클라이언트가 READY 상태입니다. 데이터 전송 시작")
    return True

# client와 WebSocket 연결 및 실시간 데이터 전송
async def websocket_handler(
    websocket: WebSocket,
    tr_id_list: list[str],
    tr_key_list: list[str]
):
    # 연결 추적
    active_websockets.add(websocket)
    try:
        if not await perform_client_handshake(websocket):
            return
        
        global global_broker_ws
        print("global_broker_ws:", global_broker_ws)
        if global_broker_ws is None:
            global_broker_ws = create_broker_ws(tr_id_list, tr_key_list)
            global_broker_ws.start()
        else:
            for tr_id, tr_key in zip(tr_id_list, tr_key_list):
                await global_broker_ws.update_subscription(True, tr_id, tr_key)
        
        try:
            while True:
                try:
                    # Use asyncio.to_thread to prevent blocking
                    code, data = await asyncio.to_thread(global_broker_ws.get)
                    if websocket.application_state == WebSocketState.CONNECTED:
                        await asyncio.sleep(0.05)
                        await websocket.send_json(data)
                    else:
                        print("⚠️ 웹소켓 연결 끊김")
                        break
                except websockets.exceptions.ConnectionClosedOK:
                    print("✅ 웹소켓 정상 종료")
                    break
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"⚠️ 웹소켓 연결 오류 (close frame 없음): {e}")
                    break
                except Exception as e:
                    print(f"⚠️ 데이터 처리 중 에러: {e}")
                    continue
        except Exception as e:
            print(f"⚠️ 웹소켓 핸들러 에러: {e}")
        finally:
            for tr_id, tr_key in zip(tr_id_list, tr_key_list):
                await global_broker_ws.update_subscription(False, tr_id, tr_key)
            
            if websocket.application_state != WebSocketState.DISCONNECTED:
                try:
                    await websocket.close()
                except Exception as e:
                    print(f"⚠️ 웹소켓 종료 중 에러: {e}")
            
            print("🧹 WebSocket 세션 종료")
    finally:
        # 연결 추적 해제
        active_websockets.discard(websocket)

@app.websocket("/H0STASP0")
async def websocket_orderbook(websocket: WebSocket):
    await websocket_handler(
        websocket,
        tr_id_list=["H0STASP0"],
        tr_key_list=["005930"]
    )

@app.websocket("/H0STCNT0")
async def websocket_execution(websocket: WebSocket):
    await websocket_handler(
        websocket,
        tr_id_list=["H0STCNT0"],
        tr_key_list=["005930"]
    )

@app.websocket("/HDFSASP0")
async def websocket_overseas_orderbook(websocket: WebSocket):
    await websocket_handler(
        websocket,
        tr_id_list=["HDFSASP0"],
        tr_key_list=["AAPL"]
    )

################### 실시간 알림 #####################

# Firestore에서 디바이스 토큰 목록 가져오기
def get_device_tokens():
    tokens_ref = db.collection('user_tokens')  # 'user_tokens' 컬렉션에서 토큰 가져오기
    tokens = tokens_ref.stream()
    
    token_list = []
    for token in tokens:
        token_list.append(token.to_dict()['token'])
    
    return token_list

# FCM 알림 전송 함수
def send_fcm_notification(tokens, title, body):
    # FCM 전용 스코프 지정
    scopes = ["https://www.googleapis.com/auth/firebase.messaging"]
    credentials, project_id = google.auth.default(scopes=scopes)
    request_obj = google.auth.transport.requests.Request()
    credentials.refresh(request_obj)
    access_token = credentials.token

    url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    headers = {
         "Authorization": f"Bearer {access_token}",
         "Content-Type": "application/json; charset=UTF-8"
    }
    
    for token in tokens:
        message = {
            "message": {
                "token": token,
                "notification": {
                    "title": title,
                    "body": body
                }
            }
        }
        response = httpx.post(url, json=message, headers=headers)
        print(f"FCM 메시지 전송 완료: {response.status_code}, {response.text}")

# 텔레그램 메시지 전송
async def notify_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    async with httpx.AsyncClient() as client:
        await client.get(url, params=params)
    print(f"텔레그램 메시지 전송 완료")

# 알림 전송 통합
async def notify_all(price: int, stock_code: str = "005930"):
    fcm_tokens = get_device_tokens()
    fcm_title = "📈 [주가 알림]"
    fcm_body = f"{stock_code} 현재가 {price}원 도달!"

    telegram_message = f"📈 [주가 알림] {stock_code} 현재가 {price}원 도달!"

    send_fcm_notification(
        tokens=fcm_tokens,
        title=fcm_title,
        body=fcm_body
    )

    # TODO: telegram ID 리스트를 가져오도록 수정
    await notify_telegram(telegram_message)

# 주식 현재가 실시간 감시
async def listen_price(tr_key_list: list = None):
    if tr_key_list is None:
        tr_key_list = ["005930"]

    tr_id_list = ["H0STOUP0"] * len(tr_key_list)

    global global_broker_ws
    global_broker_ws = create_broker_ws(tr_id_list=tr_id_list, tr_key_list=tr_key_list)
    global_broker_ws.start()
    print(f"📡 WebSocket 연결됨")

    notified_prices = {}
    last_cleanup_time = time.time()
    
    try:
        while True:
            code, data = await asyncio.to_thread(global_broker_ws.get)
            execution_codes = [
                "H0STCNT0", "H0STOUP0", "H0UPCNT0", "H0EWCNT0", "HDFSCNT0",
                "H0IOCNT0", "H0CFCNT0", "H0ZFCNT0", "H0ZOCNT0", "H0EUCNT0",
                "H0MFCNT0", "HDFFF020", "H0BJCNT0", "H0BICNT0"]
            if code in execution_codes:
                try:
                    price = int(data['현재가'])
                    code = data["유가증권단축종목코드"]
                    if code not in tr_key_list:
                        continue

                    print(f"[{code}] 현재가: {price}원")
                    current_time = time.time()
                    
                    # 만료된 알림 정리 (1분마다)
                    if current_time - last_cleanup_time > 60:
                        expired_prices = [p for p, t in notified_prices.items() 
                                         if current_time - t > NOTIFICATION_EXPIRY_TIME]
                        for p in expired_prices:
                            del notified_prices[p]
                            print(f"🔄 알림 만료: {p}원 (30분 경과)")
                        last_cleanup_time = current_time
                    
                    if price in TARGET_PRICES:
                        if price not in notified_prices or (current_time - notified_prices[price] > NOTIFICATION_EXPIRY_TIME):
                            print(f"🚨 알림: 주가가 {price}원에 도달했습니다!")
                            notified_prices[price] = current_time # 알림을 보낸 가격과 시간 기록
                            await notify_all(price)
                except (ValueError, KeyError) as e:
                    print(f"데이터 처리 오류: {e}")
                except websockets.exceptions.ConnectionClosedOK:
                    print("✅ 웹소켓 정상 종료")
                    break
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"⚠️ 웹소켓 연결 오류 (close frame 없음): {e}")
                    break
    except Exception as e:
        print(f"가격 감시 중 오류 발생: {e}")
    finally:
        # 웹소켓 프로세스 종료
        global_broker_ws.terminate()
        print("🔌 WebSocket 연결 종료")
