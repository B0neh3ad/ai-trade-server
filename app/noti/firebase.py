import google.auth
import google.auth.transport.requests
import httpx
from pydantic import BaseModel
from firebase_admin import firestore

from app.global_vars import get_cred, get_db

class FCMTokenData(BaseModel):
    userId: str
    token: str

# 디바이스 토큰 저장
async def _store_fcm_token(data: FCMTokenData):
    db = get_db()
    doc_ref = db.collection("user_tokens").document(data.userId)
    doc_ref.set({
        "token": data.token,
        "timestamp": firestore.SERVER_TIMESTAMP,
    })

# Firestore에서 디바이스 토큰 목록 가져오기
def get_device_tokens():
    db = get_db()
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