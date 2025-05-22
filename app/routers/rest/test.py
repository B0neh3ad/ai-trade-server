from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.noti import _push_notification
from app.config import db

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "KOSPI200 Futures API Server is running"}

@router.get("/push")
async def push_notification():
    content = await _push_notification(db)
    return JSONResponse(content=content)