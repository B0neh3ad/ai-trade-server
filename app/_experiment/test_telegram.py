import time
import httpx
import asyncio
import os
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

from api.api import fetch_domestic_indexfuture_price, fetch_domestic_stock_price

import google.auth
import google.auth.transport.requests
import firebase_admin
from firebase_admin import credentials, firestore

notified_prices = {}
NOTIFICATION_EXPIRY_TIME = 30 * 60  # 30분 (초 단위)
target_prices = list(range(54500, 56000, 50))

last_cleanup_time = time.time()

# 서비스 계정 키 JSON 경로
cred = credentials.Certificate("./service-account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Firestore에서 디바이스 토큰 목록 가져오기
def get_device_tokens():
    tokens_ref = db.collection('user_tokens')  # 'user_tokens' 컬렉션에서 토큰 가져오기
    tokens = tokens_ref.stream()
    
    token_list = []
    for token in tokens:
        token_list.append(token.to_dict()['token'])
    
    return token_list

# FCM 메시지 전송
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
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={message}"
    # params = {
    #     "chat_id": TELEGRAM_CHAT_ID,
    #     "text": message,
    # }
    async with httpx.AsyncClient() as client:
        await client.get(url)

# 알림 전송 통합
async def notify_all(price: int, stock_code: str = "005930"):
    fcm_tokens = get_device_tokens()
    fcm_title = "📈 [주가 알림]"
    fcm_body = f"{stock_code} 현재가 {price}원 도달!"

    telegram_message = f"📈 [주가 알림] {stock_code} 현재가 {price}원 도달!"
    print("tokens: ", fcm_tokens)
    send_fcm_notification(
        tokens=fcm_tokens,
        title=fcm_title,
        body=fcm_body
    )

    # TODO: telegram ID 리스트를 가져오도록 수정
    await notify_telegram(telegram_message)

async def test_telegram():
    global last_cleanup_time

    data = fetch_domestic_stock_price()

    try:
        price = float(data["output"]["stck_prpr"]) # 국내 주식
    except KeyError:
        price = float(data["output3"]["bstp_nmix_prpr"])
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

    if price in target_prices:
        if price not in notified_prices \
        or (current_time - notified_prices[price] > NOTIFICATION_EXPIRY_TIME):
            print(f"🚨 알림: 주가가 {price}원에 도달했습니다!")
            notified_prices[price] = current_time # 알림을 보낸 가격과 시간 기록
            await notify_all(price)

# 실행
if __name__ == "__main__":
    asyncio.run(test_telegram())
