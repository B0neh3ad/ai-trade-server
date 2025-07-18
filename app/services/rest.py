from app.brokers.KoreaInvestment import KoreaInvestmentPlus
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

def fetch_domestic_futureoption_price(market_div_code: str, symbol: str, print_log: bool = False) -> dict:
    """선물옵션 현재가 조회"""
    data = broker.fetch_domestic_futureoption_price(market_div_code, symbol)
    if print_log:
        print("[선물옵션 현재가]", data)
    return data

def fetch_domestic_futureoption_asking_price(market_div_code: str, symbol: str, print_log: bool = False) -> dict:
    """선물옵션 시세호가 조회"""
    data = broker.fetch_domestic_futureoption_asking_price(market_div_code, symbol)
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

def fetch_domestic_futureoption_time_fuopchartprice(market_div_code: str, symbol: str, date: str, hour: str,
                                                       hour_class_code: str,
                                                       include_pw_data: bool,
                                                       print_log: bool = False) -> dict:
    """선물옵션 분봉조회"""
    data = broker.fetch_domestic_futureoption_time_fuopchartprice(
        market_div_code, symbol, date, hour, hour_class_code, include_pw_data
    )
    if print_log:
        print("[선물옵션 분봉조회]", data)
    return data

def fetch_domestic_futureoption_daily_fuopchartprice(market_div_code: str, symbol: str, start_date: str,
                                                       end_date: str, period_div_code: str,
                                                       print_log: bool = False) -> dict:
    """선물옵션 기간별 시세"""
    data = broker.fetch_domestic_futureoption_daily_fuopchartprice(
        market_div_code, symbol, start_date, end_date, period_div_code
    )
    if print_log:
        print("[선물옵션 기간별 시세]", data)
    return data

