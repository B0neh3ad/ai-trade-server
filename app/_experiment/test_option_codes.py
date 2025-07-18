import numpy as np
from typing import List, Set

from app.services.rest import fetch_domestic_futureoption_price


def get_target_option_codes(tr_key: str) -> List[str]:
    """
    ATM 부근 option code 반환
    (pooling 함수에서 1초에 1번씩 호출될 예정)
    - monthly: 콜 10개, 풋 10개
        - 콜, 풋 둘다 등가격에서 1개 내가격 선에서부터 10개 가져오기
    - weekly: 콜 5개, 풋 5개
        - 콜, 풋 둘다 등가격에서 1개 내가격 선에서부터 5개 가져오기
        - 예) 등가격 410인 경우
            - 콜: 407.5 410 412.5 415 417.5
            - 풋: 412.5 410 407.5 405 402.5
    """
    # TODO: masterfile에서 가져오게 하기
    strike_prices = np.arange(185, 500, 2.5)
    n = len(strike_prices)

    index = fetch_domestic_futureoption_price(tr_key)["output3"]["bstp_nmix_prpr"] # KOSPI200 지수 현재가

    atm_idx = min(range(n), key=lambda i: abs(strike_prices[i] - index))

    selected_strikes = strike_prices[max(0, atm_idx - 10) : min(n, atm_idx + 10)]
    option_codes = [f"{tr_key}{int(strike):03d}" for strike in selected_strikes]
    return option_codes

# option에 대해서는 option - 실제 구독종목 목록 dict 만들어야 되나
async def update_option_subscriptions(tr_key: str, new_option_codes: Set[str]):
    pass