import mojito
from config import APP_KEY, APP_SECRET, ACC_NO
from .broker import KoreaInvestmentPlus, KoreaInvestmentWSPlus

broker = KoreaInvestmentPlus(
    api_key=APP_KEY,
    api_secret=APP_SECRET,
    acc_no=ACC_NO
)

def create_broker_ws(tr_id_list: list = None, tr_key_list: list = None, user_id: str = None):
    """
    웹소켓 통신을 위한 증권사 객체
    :param tr_id_list: 메세지 종류
        H0STASP0: 국내주식 호가
        H0STCNT0: 국내주식 체결
        H0STCNI0: 국내주식 체결통보(고객용)
        H0STCNI9: 국내주식 체결통보(모의)

        H0IFASP0: 국내지수선물 호가
    :param tr_key_list: 메세지를 받을 종목코드
    :param user_id: 체결통보용 htsid
    """
    if tr_id_list is None:
        tr_id_list = ['H0IFASP0'] # 국내지수선물호가

    if tr_key_list is None:
        tr_key_list = ["101S12"] # KOSPI200 지수선물

    broker_ws = KoreaInvestmentWSPlus(
        api_key=APP_KEY,
        api_secret=APP_SECRET,
        tr_id_list=tr_id_list,
        tr_key_list=tr_key_list,
        user_id=user_id  # 체결통보용 htsid
    )
    return broker_ws

def fetch_stock_price(symbol: str = "005930") -> dict:
    """주식 현재가 조회"""
    return broker.fetch_price(symbol)

def fetch_futureoption_price(market_code: str = "F", symbol: str = "101S03") -> dict:
    """선물옵션 현재가 조회"""
    return broker.fetch_futureoption_price(market_code, symbol)

if __name__ == "__main__":
    print(fetch_stock_price())  # 테스트 실행

