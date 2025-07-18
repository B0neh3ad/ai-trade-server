import httpx
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

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