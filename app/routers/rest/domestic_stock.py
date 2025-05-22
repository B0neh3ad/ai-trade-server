from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.api import fetch_domestic_stock_price

router = APIRouter()

@router.get("/domestic-stock/price")
async def get_domestic_stock_price(symbol: str = "005930"):
    data = fetch_domestic_stock_price(symbol)
    return JSONResponse(content=data)