from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.services.rest import fetch_display_board_callput, fetch_display_board_option_list, fetch_domestic_futureoption_asking_price, fetch_domestic_futureoption_price, fetch_domestic_stock_price
from app.global_vars import get_broker_ws
from app._noti.firebase import FCMTokenData, _store_fcm_token
from app._noti.main import _push_notification
from app.routers.rest.database import router as database_router

router = APIRouter()

# Include database routes
router.include_router(database_router, prefix="/database", tags=["database"])

@router.get("/domestic-stock/price")
async def get_domestic_stock_price(symbol: str = "005930"):
    data = fetch_domestic_stock_price(symbol)
    return JSONResponse(content=data)

@router.get("/domestic-futureoption/price")
async def get_domestic_futureoption_price(market_code: str = "F", symbol: str = "101W09"):
    data = fetch_domestic_futureoption_price(market_code, symbol)
    return JSONResponse(content=data)

@router.get("/domestic-futureoption/asking-price")
async def get_domestic_futureoption_asking_price(market_code: str = "F", symbol: str = "101W09"):
    data = fetch_domestic_futureoption_asking_price(market_code, symbol)
    return JSONResponse(content=data)

@router.get("/domestic-futureoption/display-board-option-list")
async def get_domestic_futureoption_display_board_option_list():
    data = fetch_display_board_option_list()
    return JSONResponse(content=data)

@router.get("/domestic-futureoption/display-board-callput")
async def get_domestic_futureoption_display_board_callput(market_class_code: str = "", maturity_contract: str = "202507"):
    print(f"[get_domestic_futureoption_display_board_callput] market_class_code: {market_class_code}, maturity_contract: {maturity_contract}")
    data = fetch_display_board_callput(market_class_code, maturity_contract)
    return JSONResponse(content=data)

@router.get("/domestic-futureoption/options-info")
async def get_domestic_futureoption_options_info():
    """
    broker_ws에서 구독 중인 선물/옵션 정보 반환
    - 최근월 옵션, (위클리 옵션)
    """
    broker_ws = get_broker_ws()
    if broker_ws is None:
        raise HTTPException(status_code=500, detail="Broker WebSocket is not connected")
    
    return broker_ws.get_options_info()

@router.get("/domestic-futureoption/futures-info")
async def get_domestic_futureoption_futures_info():
    broker_ws = get_broker_ws()
    if broker_ws is None:
        raise HTTPException(status_code=500, detail="Broker WebSocket is not connected")
    
    return broker_ws.get_futures_info()

@router.post("/fcmtoken")
async def store_fcm_token(data: FCMTokenData):
    try:
        await _store_fcm_token(data)
        return {"message": "Token stored successfully"}
    except Exception as e:
        print(f"Error storing FCM token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

### Test APIs ###

@router.get("/")
async def root():
    return {"message": "KOSPI200 Futures API Server is running"}

@router.get("/push")
async def push_notification():
    content = await _push_notification()
    return JSONResponse(content=content)