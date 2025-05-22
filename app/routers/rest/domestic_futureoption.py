from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.api import fetch_domestic_indexfuture_price

router = APIRouter()

@router.get("/domestic-indexfuture/price")
async def get_domestic_indexfuture_price(market_code: str = "F", symbol: str = "101W06"):
    data = fetch_domestic_indexfuture_price(market_code, symbol)
    return JSONResponse(content=data)