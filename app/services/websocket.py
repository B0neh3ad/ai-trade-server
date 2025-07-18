import json
from typing import Dict, Set
from fastapi import WebSocket
import numpy as np
import websockets
from starlette.websockets import WebSocketState, WebSocketDisconnect
import asyncio
from dataclasses import asdict

from app.brokers.KoreaInvestment.main import KoreaInvestmentWSPlus
from app.services.rest import fetch_domestic_futureoption_price
from app.global_vars import get_broker_ws
from app.db.database import get_kospi_database

# Global subscribers dictionary
subscribers: Dict[str, Set[WebSocket]] = {}

# manage_subscription: client -> server 방향으로 subscription info 전달
async def manage_subscription(websocket: WebSocket):
    broker_ws = get_broker_ws()

    my_subscriptions: Set[str] = set()

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            print("[Received Message from Client]")
            print(msg)
            
            msg_type = msg.get("type")
            tr_id = msg.get("tr_id")
            tr_key = msg.get("tr_key")

            if not (msg_type and tr_id and tr_key):
                continue
                
            key = f"{tr_id}:{tr_key}"

            if msg_type == "subscribe":
                subscribers.setdefault(key, set()).add(websocket)
                my_subscriptions.add(key)

                # option은 서버 시작 시 구독되므로, update_subscription이 실행되지 않는다.
                # 실행되더라도, 증권사 입장에서는 유효하지 않은 tr_id이므로 무시된다.
                if key not in broker_ws.subscribed_to_broker:
                    await broker_ws.update_subscription(True, tr_id, tr_key)
                    print(f"Broker subscribe: {key}")
            
            elif msg_type == "unsubscribe":
                if key in subscribers and websocket in subscribers[key]:
                    subscribers[key].remove(websocket)
                    my_subscriptions.discard(key)
                    # if not subscribers[key]:
                    #     await broker_ws.update_subscription(False, tr_id, tr_key)
                    print(f"Broker unsubscribe: {key}")

            print(f"Subscribers updated: {subscribers}")

    except WebSocketDisconnect:
        print("Client disconnected")

        for key in my_subscriptions:
            if websocket in subscribers.get(key, set()):
                subscribers[key].remove(websocket)

                if not subscribers[key]:
                    await broker_ws.update_subscription(False, tr_id, tr_key)
                    print(f"Broker unsubscribe: {key}")


# broadcast_data: server -> client 방향으로 subscribed info 전달
async def broadcast_data(print_log: bool = False):    
    broker_ws = get_broker_ws()
    kospi_db = get_kospi_database()
    
    if broker_ws is None:
        return

    try:
        key = None
        while True:
            try:
                data = await broker_ws.get()
                if data is None:
                    continue
                    
                tr_id, tr_key, parsed_data = data
                key = f"{tr_id}:{tr_key}"
                
                # Store data in database
                try:
                    await kospi_db.add_data(tr_id, tr_key, parsed_data)
                except Exception as e:
                    print(f"⚠️ 데이터베이스 저장 중 에러: {e}")
                
                for websocket in subscribers.get(key, set()).copy():
                    if websocket.application_state == WebSocketState.CONNECTED:
                        data_dict = asdict(parsed_data)
                        send_data = {
                            "key": key,
                            "data": data_dict
                        }
                        if print_log:
                            print("[Data (server -> client)]")
                            print(send_data)
                        await asyncio.sleep(0.05)
                        try:
                            await websocket.send_json(send_data)
                        except Exception as e:
                            err_msg = str(e)
                            print(f"⚠️ 웹소켓 데이터 전송 중 에러: {err_msg}")
                            # 특정 에러 메시지일 때만 제거
                            if "Unexpected ASGI message 'websocket.send'" in err_msg:
                                subscribers[key].remove(websocket)
                            continue
                    else:
                        print(f"⚠️ 웹소켓 연결 끊김: {websocket}")
                        subscribers[key].remove(websocket)
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
        print("WebSocket 세션 종료")


### 옵션 관련 ###

def get_target_option_codes(
        index: float, option_key: str, weekly: bool = False
        ) -> Set[str]:
    """
    ATM 부근 option code 반환
    (pooling 함수에서 1초에 1번씩 호출될 예정)
    - monthly: 콜 10개, 풋 10개
        - 콜, 풋 둘다 등가격에서 1개 내가격 선에서부터 10개 가져오기
    - weekly: 콜 5개, 풋 5개
        - 콜, 풋 둘다 등가격에서 1개 내가격 선에서부터 5개 가져오기
        - 예) 등가격 410인 경우
            - 콜: 407.5 410 412.5 415 417.5
            - 풋: 402.5 405 407.5 410 412.5
    """
    index = round(float(index) / 2.5) * 2.5 # 2.5원 단위로 변환
    
    cnt = 5 if weekly else 10
    
    call_strikes = np.arange(index - 2.5, index + 2.5 * (cnt - 1), 2.5)
    put_strikes = np.arange(index - 2.5 * (cnt - 2), index + 2.5 * 2, 2.5)

    call_option_codes = set([f"2{option_key}{int(strike):03d}" for strike in call_strikes])
    put_option_codes = set([f"3{option_key}{int(strike):03d}" for strike in put_strikes])

    return call_option_codes | put_option_codes


# KOSPI200 지수옵션의 구독 관리
async def update_option_subscriptions():
    broker_ws = get_broker_ws()
    if broker_ws is None:
        return
    
    recent_future_code = broker_ws.futureoptions_info.futures[0].code
    
    while True:
        index = fetch_domestic_futureoption_price("F", recent_future_code)["output3"]["bstp_nmix_prpr"] # KOSPI200 지수 현재가
        for option in broker_ws.futureoptions_info.options:
            await broker_ws.update_option_subscriptions(
                option.code,
                get_target_option_codes(index, option.code, weekly = option.market_class_code != "")
            )
        await asyncio.sleep(2)