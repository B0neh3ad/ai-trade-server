import time
import httpx
import asyncio
import os
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

from api.api import fetch_domestic_futureoption_price, fetch_domestic_stock_price

notified_prices = {}
NOTIFICATION_EXPIRY_TIME = 30 * 60  # 30분 (초 단위)
target_prices = list(range(55000, 56000, 100))

last_cleanup_time = time.time()

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
    message = f"📈 [주가 알림] {stock_code} 현재가: {price}원 도달!"
    # await notify_websocket_clients(message)
    await notify_telegram(message)

async def test_telegram():
    global last_cleanup_time

    data = fetch_domestic_futureoption_price()

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
