from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.api.rest import fetch_domestic_futureoption_price, fetch_domestic_stock_price
from app.noti.main import _push_notification

from .firebase import _store_fcm_token, FCMTokenData
from app.global_vars import db

router = APIRouter()

@router.get("/domestic-futureoption/price")
async def get_domestic_futureoption_price(market_code: str = "F", symbol: str = "101W06"):
    data = fetch_domestic_futureoption_price(market_code, symbol)
    return JSONResponse(content=data)

@router.get("/domestic-stock/price")
async def get_domestic_stock_price(symbol: str = "005930"):
    data = fetch_domestic_stock_price(symbol)
    return JSONResponse(content=data)

@router.post("/fcmtoken")
async def store_fcm_token(data: FCMTokenData):
    try:
        _store_fcm_token(data)
        return {"message": "Token stored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/")
async def root():
    return {"message": "KOSPI200 Futures API Server is running"}

@router.get("/push")
async def push_notification():
    content = await _push_notification(db)
    return JSONResponse(content=content)