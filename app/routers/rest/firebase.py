from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from firebase_admin import firestore
from app.global_vars import db

router = APIRouter()

class FCMTokenData(BaseModel):
    userId: str
    token: str
    
async def _store_fcm_token(data: FCMTokenData):
    doc_ref = db.collection("user_tokens").document(data.userId)
    doc_ref.set({
        "token": data.token,
        "timestamp": firestore.SERVER_TIMESTAMP,
    })