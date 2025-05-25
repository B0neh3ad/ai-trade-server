import json
import time
from typing import Dict, Set
from fastapi import WebSocket
import websockets
from starlette.websockets import WebSocketState, WebSocketDisconnect

import asyncio

from dataclasses import asdict

from app.global_vars import get_broker_ws

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
                if key not in broker_ws.subscribed_to_broker:
                    await broker_ws.update_subscription(True, tr_id, tr_key)
                    print(f"Broker subscribe: {key}")
            
            elif msg_type == "unsubscribe":
                if key in subscribers and websocket in subscribers[key]:
                    subscribers[key].remove(websocket)
                    my_subscriptions.discard(key)
                    if not subscribers[key]:
                        await broker_ws.update_subscription(False, tr_id, tr_key)
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
async def broadcast_data():    
    broker_ws = get_broker_ws()
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
                
                for websocket in subscribers.get(key, set()).copy():
                    if websocket.application_state == WebSocketState.CONNECTED:
                        data_dict = asdict(parsed_data)
                        send_data = {
                            "key": key,
                            "data": data_dict
                        }
                        # print("[Data (server -> client)]")
                        # print(send_data)
                        await asyncio.sleep(0.05)
                        try:
                            await websocket.send_json(send_data)
                        except Exception as e:
                            print(f"⚠️ 웹소켓 데이터 전송 중 에러: {e}")
                            print(f"Subscribers[key]: {subscribers.get(key, set()).copy()}")
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