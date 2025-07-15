from app.config import APP_KEY, APP_SECRET
from app.api.broker import KoreaInvestmentWSPlus


def create_broker_ws(code_list: list = None, user_id: str = None):
    """
    웹소켓 통신을 위한 증권사 객체
    :param code_list: 초기 메세지 종류
    :param user_id: 체결통보용 htsid
    """
    
    broker_ws = KoreaInvestmentWSPlus(
        api_key=APP_KEY,
        api_secret=APP_SECRET,
        code_list=code_list,
        user_id=user_id  # 체결통보용 htsid
    )
    return broker_ws