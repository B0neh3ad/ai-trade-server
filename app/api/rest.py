from app.api.broker import KoreaInvestmentPlus
from app.config import APP_KEY, APP_SECRET, ACC_NO

broker = KoreaInvestmentPlus(
    api_key=APP_KEY,
    api_secret=APP_SECRET,
    acc_no=ACC_NO
)

def fetch_domestic_stock_price(symbol: str, print_log: bool = False) -> dict:
    """주식 현재가 조회"""
    data = broker.fetch_price(symbol)
    if print_log:
        print("[주식 현재가]", data)
    return data

def fetch_domestic_futureoption_price(market_code: str, symbol: str, print_log: bool = False) -> dict:
    """선물옵션 현재가 조회"""
    data = broker.fetch_domestic_futureoption_price(market_code, symbol)
    if print_log:
        print("[선물옵션 현재가]", data)
    return data

def fetch_domestic_futureoption_asking_price(market_code: str, symbol: str, print_log: bool = False) -> dict:
    """선물옵션 시세호가 조회"""
    data = broker.fetch_domestic_futureoption_asking_price(market_code, symbol)
    if print_log:
        print("[선물옵션 시세호가]", data)
    return data

def fetch_display_board_option_list(print_log: bool = False) -> dict:
    """옵션전광판 옵션월물리스트 조회"""
    data = broker.fetch_display_board_option_list()
    if print_log:
        print("[옵션전광판 옵션월물리스트 조회]", data)
    return data

def fetch_display_board_callput(market_class_code: str, maturity_contract: str, print_log: bool = False) -> dict:
    """옵션전광판 콜풋 조회"""
    data = broker.fetch_display_board_callput(market_class_code, maturity_contract)
    if print_log:
        print("[옵션전광판 콜풋 조회]", data)
    return data