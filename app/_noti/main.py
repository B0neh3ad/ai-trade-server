from app.global_vars import get_db
from app._noti.firebase import get_device_tokens, send_fcm_notification
from app._noti.telegram import notify_telegram

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

async def _push_notification():
    fcm_tokens = get_device_tokens()
    fcm_title = "Recommendation"
    fcm_body = "State_30_D, State_5_Z, State_20_U\\nRecommendations: 콜360 1개 short, 풋 360 1개 short, 풋 355 1개 long"

    print("디바이스 토큰 목록:", fcm_tokens)
    
    send_fcm_notification(
        tokens=fcm_tokens,
        title=fcm_title,
        body=fcm_body
    )
    
    return {"message": "Push notification sent"}