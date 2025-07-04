from app.api.broker import KoreaInvestmentPlus
from app.config import APP_KEY, APP_SECRET, ACC_NO

broker = KoreaInvestmentPlus(
    api_key=APP_KEY,
    api_secret=APP_SECRET,
    acc_no=ACC_NO
)

def fetch_domestic_stock_price(symbol: str) -> dict:
    """주식 현재가 조회"""
    data = broker.fetch_price(symbol)
    print("[주식 현재가]", data)
    return data

def fetch_domestic_futureoption_price(market_code: str, symbol: str) -> dict:
    """선물옵션 현재가 조회"""
    data = broker.fetch_domestic_futureoption_price(market_code, symbol)
    print("[선물옵션 현재가]", data)
    return data

def fetch_domestic_futureoption_asking_price(market_code: str, symbol: str) -> dict:
    """선물옵션 시세호가 조회"""
    data = broker.fetch_domestic_futureoption_asking_price(market_code, symbol)
    print("[선물옵션 시세호가]", data)
    return data

def fetch_display_board_callput(market_class_code: str, maturity_contract: str) -> dict:
    """옵션전광판 콜풋 조회"""
    data = broker.fetch_display_board_callput(market_class_code, maturity_contract)
    print("[옵션전광판 콜풋 조회]")
    return data