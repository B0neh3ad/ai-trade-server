from app.config import APP_KEY, APP_SECRET
from app.api.broker import KoreaInvestmentWSPlus


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
    
    broker_ws = KoreaInvestmentWSPlus(
        api_key=APP_KEY,
        api_secret=APP_SECRET,
        tr_id_list=tr_id_list,
        tr_key_list=tr_key_list,
        user_id=user_id  # 체결통보용 htsid
    )
    return broker_ws