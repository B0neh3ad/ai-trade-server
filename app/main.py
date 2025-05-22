from fastapi import FastAPI, WebSocket

from contextlib import asynccontextmanager
import asyncio
import threading

import websockets
from starlette.websockets import WebSocketState, WebSocketDisconnect

import signal
import time

from api import *
from app.noti import notify_all
from app.utils import signal_handler
from app.global_vars import global_broker_ws, active_websockets

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

def start_listen_indexfuture_price():
    asyncio.run(listen_indexfuture_price())

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: realtime_ws 시작
    # lp_thread = threading.Thread(target=start_listen_price, daemon=True)
    # lp_thread.start()
    lp_thread = threading.Thread(target=start_listen_indexfuture_price, daemon=True)
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
                    try:
                        # close frame 전송 시도
                        await websocket.close(code=1000, reason="Sending close frame manually")
                        print("✅ 직접 close frame 전송 완료")
                    except Exception as err:
                        print(f"❗ close frame 전송 중 오류: {err}")
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


################### 실시간 감시/알림 #####################

# 주식 현재가 실시간 감시
async def listen_price(tr_key_list: list = None):
    if tr_key_list is None:
        tr_key_list = ["005930"]

    tr_id_list = ["H0STCNT0"] * len(tr_key_list)

    global global_broker_ws
    global_broker_ws = create_broker_ws(tr_id_list=tr_id_list, tr_key_list=tr_key_list)
    global_broker_ws.start()
    print("📡 WebSocket 연결됨")

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
                    price = float(data['현재가'])
                    code = data["종목코드"]

                    # TODO: 구독한 종목이 아니면 건너뛰기

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
                            await notify_all(price, firebase_db=db)
                except (ValueError, KeyError) as e:
                    print(f"데이터 처리 오류: {e}")
                except websockets.exceptions.ConnectionClosedOK:
                    print("✅ 웹소켓 정상 종료")
                    break
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"⚠️ 웹소켓 연결 오류 (close frame 없음): {e}")
                    try:
                        # close frame 전송 시도
                        await global_broker_ws.websocket.close(code=1000, reason="Sending close frame manually")
                        print("✅ 직접 close frame 전송 완료")
                    except Exception as err:
                        print(f"❗ close frame 전송 중 오류: {err}")
                    break
    except Exception as e:
        print(f"가격 감시 중 오류 발생: {e}")
    finally:
        # 웹소켓 프로세스 종료
        global_broker_ws.terminate()
        print("🔌 WebSocket 연결 종료")

# 지수선물 현재가 실시간 감시
async def listen_indexfuture_price(tr_key_list: list = None):
    if tr_key_list is None:
        tr_key_list = ["101W06"]

    tr_id_list = ["H0IFCNT0"] * len(tr_key_list)

    global global_broker_ws
    global_broker_ws = create_broker_ws(tr_id_list=tr_id_list, tr_key_list=tr_key_list)
    global_broker_ws.start()
    print("📡 WebSocket 연결됨")

    notified_prices = {}
    last_cleanup_time = time.time()
    
    try:
        while True:
            code, data = await asyncio.to_thread(global_broker_ws.get)
            # 지수선물 체결가 코드
            execution_codes = ["H0IFCNT0"]
            if code in execution_codes:
                try:
                    price = float(data['현재가'])
                    code = data["종목코드"]

                    # TODO: 구독한 종목이 아니면 건너뛰기

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
                    try:
                        # close frame 전송 시도
                        await global_broker_ws.websocket.close(code=1000, reason="Sending close frame manually")
                        print("✅ 직접 close frame 전송 완료")
                    except Exception as err:
                        print(f"❗ close frame 전송 중 오류: {err}")
                    break
    except Exception as e:
        print(f"가격 감시 중 오류 발생: {e}")
    finally:
        # 웹소켓 프로세스 종료
        global_broker_ws.terminate()
        print("🔌 WebSocket 연결 종료")