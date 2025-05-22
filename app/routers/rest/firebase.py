from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from firebase_admin import firestore
from app.config import db

router = APIRouter()

class FCMTokenData(BaseModel):
    userId: str
    token: str

@router.post("/fcmtoken")
async def store_fcm_token(data: FCMTokenData):
    try:
        # Firestore에 user_tokens 컬렉션에 저장 (userId를 document id로 사용)
        doc_ref = db.collection("user_tokens").document(data.userId)
        doc_ref.set({
            "token": data.token,
            "timestamp": firestore.SERVER_TIMESTAMP,
        })
        return {"message": "Token stored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))