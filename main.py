import threading
from fastapi import FastAPI, WebSocket
import asyncio
import httpx
from starlette.websockets import WebSocketState
from fastapi.responses import JSONResponse
import signal
import sys
from multiprocessing import Process
import time
import websockets
import requests

from api.api import *
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from utils import signal_handler

import firebase_admin
from firebase_admin import credentials, firestore, messaging

app = FastAPI()

# 활성화된 브로커 목록
active_brokers: list[Process] = []

# 주가 감시 설정
NOTIFICATION_EXPIRY_TIME = 30 * 60  # 30분 (초 단위)
TARGET_PRICES = list(range(55000, 56000, 100))

# 서비스 계정 키 JSON 경로
cred = credentials.Certificate("./service-account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

################### REST API #####################

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

@app.get("/")
async def root():
    return {"message": "KOSPI200 Futures API Server is running"}

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
    """
    클라이언트와의 WebSocket 핸드셰이크를 수행합니다.
    
    Args:
        websocket: WebSocket 연결 객체
        
    Returns:
        bool: 핸드셰이크 성공 여부
    """
    await websocket.accept()

    try:
        init_msg = await asyncio.wait_for(websocket.receive_text(), timeout=5)
    except asyncio.TimeoutError:
        print("⏰ 클라이언트가 READY를 보내지 않아서 연결 종료")
        await websocket.close()
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
    # 클라이언트와 핸드셰이크 수행
    if not await perform_client_handshake(websocket):
        return

    broker_ws = create_broker_ws(tr_id_list, tr_key_list)
    broker_ws.start()

    # Add the broker to the active brokers list
    active_brokers.append(broker_ws)
    
    try:
        while True:
            try:
                # Use asyncio.to_thread to prevent blocking
                data_type, data = await asyncio.to_thread(broker_ws.get)

                if websocket.application_state == WebSocketState.CONNECTED:
                    await asyncio.sleep(0.05)
                    await websocket.send_json(data)
                else:
                    print("⚠️ 웹소켓 연결 끊김")
                    break
            except websockets.exceptions.ConnectionClosedError:
                print("⚠️ 웹소켓 연결이 예기치 않게 종료됨")
                break
            except Exception as e:
                print(f"⚠️ 데이터 처리 중 에러: {e}")
                continue
    except Exception as e:
        print(f"⚠️ 웹소켓 핸들러 에러: {e}")
    finally:
        # Remove the broker from the active brokers list
        if broker_ws in active_brokers:
            active_brokers.remove(broker_ws)
            if broker_ws.is_alive():
                print(f"Terminating broker process {broker_ws.pid}")
                broker_ws.terminate()
                broker_ws.join(timeout=2)
                if broker_ws.is_alive():
                    print(f"Force killing broker process {broker_ws.pid}")
                    broker_ws.kill()
        
        if websocket.application_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.close()
            except Exception as e:
                print(f"⚠️ 웹소켓 종료 중 에러: {e}")
        
        print("🧹 WebSocket 세션 종료")

@app.websocket("/H0STASP0")
async def websocket_orderbook(websocket: WebSocket):
    await websocket_handler(
        websocket,
        tr_id_list=["H0STASP0"],
        tr_key_list=["005930"]
    )

@app.websocket("/HOSTCNT0")
async def websocket_execution(websocket: WebSocket):
    await websocket_handler(
        websocket,
        tr_id_list=["HOSTCNT0"],
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
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        tokens=tokens
    )
    response = messaging.send_multicast(message)
    print(f"FCM 메시지 전송 완료: {response}")


# 텔레그램 메시지 전송
async def notify_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)

# 알림 전송 통합
async def notify_all(price: int, stock_code: str = "005930"):
    fcm_tokens = get_device_tokens()
    fcm_title = "📈 [주가 알림]"
    fcm_body = f"{stock_code} 현재가: {price}원 도달!"

    telegram_message = f"📈 [주가 알림] {stock_code} 현재가: {price}원 도달!"

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
        
    broker_ws = create_broker_ws(
        tr_id_list=["H0STASP0"],  # 실시간 체결
        tr_key_list=tr_key_list    # 삼성전자
    )
    broker_ws.start()
    print(f"📡 WebSocket 연결됨: 005930 실시간 감시 시작")
    
    # 이미 알림을 보낸 가격을 추적하기 위한 딕셔너리 (가격: 타임스탬프)
    notified_prices = {}
    
    # 마지막 정리 시간
    last_cleanup_time = time.time()
    
    try:
        while True:
            data_type, data = broker_ws.get()
            
            if data_type == '체결':
                try:
                    price = int(data['주식현재가'])
                    print(f"[005930] 현재가: {price}원")
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
    except Exception as e:
        print(f"가격 감시 중 오류 발생: {e}")
    finally:
        # 웹소켓 프로세스 종료
        broker_ws.terminate()
        print("🔌 WebSocket 연결 종료")

# @app.on_event("startup")
# def start_realtime_ws():
#     thread = threading.Thread(target=lambda: asyncio.run(listen_price()))
#     thread.daemon = True
#     thread.start()