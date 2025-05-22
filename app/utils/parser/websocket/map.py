from typing import Type
from dataclasses import dataclass
from enum import Enum

from app.utils.parser.websocket.domestic_cme_future import *
from app.utils.parser.websocket.domestic_index_future import *

class MessageType(Enum):
    EXECUTION = "execution"
    ORDERBOOK = "orderbook"
    NOTICE = "notice"

@dataclass(frozen=True)
class TRMeta:
    type: MessageType
    model: Type

'''
code별 response dataclass 추가 시 아래 코드(또는 _experiment/test_websocket.py) 참고
https://github.com/koreainvestment/open-trading-api/blob/main/websocket/python/ws_domestic_overseas_all.py
'''
TR_CODE_MAP = {
    ### 국내 지수선물 ###
    "H0IFASP0": TRMeta(
        MessageType.ORDERBOOK,
        DomesticIndexFutureOrderbookResponse,
    ),
    "H0IFCNT0": TRMeta(
        MessageType.EXECUTION,
        DomesticIndexFutureExecutionResponse,
    ), 
    "H0IFCNI0": TRMeta(
        MessageType.NOTICE,
        DomesticIndexFutureNoticeResponse,
    ),
    "H0IFCNI9": TRMeta( # 모의투자
        MessageType.NOTICE,
        DomesticIndexFutureNoticeResponse,
    ),

    ### 국내 야간선물(CME) ###
    "H0MFASP0": TRMeta(
        MessageType.ORDERBOOK,
        DomesticCMEFutureOrderbookResponse,
    ), 
    "H0MFCNT0": TRMeta(
        MessageType.EXECUTION,
        DomesticCMEFutureExecutionResponse,
    ),
    "H0MFCNI0": TRMeta(
        MessageType.NOTICE,
        DomesticCMEFutureNoticeResponse,
    )
}