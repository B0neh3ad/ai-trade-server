from app.api.broker import KoreaInvestmentPlus
from app.config import APP_KEY, APP_SECRET, ACC_NO

broker = KoreaInvestmentPlus(
    api_key=APP_KEY,
    api_secret=APP_SECRET,
    acc_no=ACC_NO
)

def fetch_domestic_stock_price(symbol: str = "005930") -> dict:
    """주식 현재가 조회"""
    data = broker.fetch_price(symbol)
    print("[주식 현재가]", data)
    return data

def fetch_domestic_indexfuture_price(market_code: str = "F", symbol: str = "101W06") -> dict:
    """선물옵션 현재가 조회"""
    data = broker.fetch_futureoption_price(market_code, symbol)
    print("[선물옵션 현재가]", data)
    return data

def fetch_overseas_stock_price(symbol: str = "AAPL") -> dict:
    """해외주식 현재가 조회"""
    data = broker.fetch_oversea_price(symbol)
    print("[해외주식 현재가]", data)
    return data