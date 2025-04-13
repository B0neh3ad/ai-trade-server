import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 한국투자증권 API 정보
API_BASE_URL = "https://openapi.koreainvestment.com:9443"
APP_KEY = os.getenv("APP_KEY")  # 환경변수에서 불러오기
APP_SECRET = os.getenv("APP_SECRET")
ACC_NO = os.getenv("ACC_NO")

# 텔레그램 메시지 전송 정보
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
