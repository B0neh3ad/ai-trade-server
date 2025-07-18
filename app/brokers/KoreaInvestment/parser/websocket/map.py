from typing import Type
from dataclasses import dataclass
from enum import Enum

from app.brokers.KoreaInvestment.parser.websocket.domestic_cme_future import *
from app.brokers.KoreaInvestment.parser.websocket.domestic_eurex_option import DomesticEurexOptionExecutionResponse, DomesticEurexOptionNoticeResponse, DomesticEurexOptionOrderbookResponse
from app.brokers.KoreaInvestment.parser.websocket.domestic_index_future import *
from app.brokers.KoreaInvestment.parser.websocket.domestic_index_option import DomesticIndexOptionExecutionResponse, DomesticIndexOptionOrderbookResponse

class InstrumentType(Enum):
    FUTURE = "future"
    OPTION = "option"

class MessageType(Enum):
    EXECUTION = "execution"
    ORDERBOOK = "orderbook"
    NOTICE = "notice"

@dataclass(frozen=True)
class TRMeta:
    instrument_type: InstrumentType
    message_type: MessageType
    model: Type

'''
code별 response dataclass 추가 시 아래 코드(또는 _experiment/test_websocket.py) 참고
https://github.com/koreainvestment/open-trading-api/blob/main/websocket/python/ws_domestic_overseas_all.py
'''
TR_ID_MAP = {
    ### 국내 지수선물 ###
    "H0IFASP0": TRMeta(
        InstrumentType.FUTURE,
        MessageType.ORDERBOOK,
        DomesticIndexFutureOrderbookResponse,
    ),
    "H0IFCNT0": TRMeta(
        InstrumentType.FUTURE,
        MessageType.EXECUTION,
        DomesticIndexFutureExecutionResponse,
    ), 
    "H0IFCNI0": TRMeta(
        InstrumentType.FUTURE,
        MessageType.NOTICE,
        DomesticIndexFutureNoticeResponse,
    ),
    "H0IFCNI9": TRMeta( # 모의투자
        InstrumentType.FUTURE,
        MessageType.NOTICE,
        DomesticIndexFutureNoticeResponse,
    ),

    ### 국내 야간선물(CME) ###
    "H0MFASP0": TRMeta(
        InstrumentType.FUTURE,
        MessageType.ORDERBOOK,
        DomesticCMEFutureOrderbookResponse,
    ), 
    "H0MFCNT0": TRMeta(
        InstrumentType.FUTURE,
        MessageType.EXECUTION,
        DomesticCMEFutureExecutionResponse,
    ),
    "H0MFCNI0": TRMeta(
        InstrumentType.FUTURE,
        MessageType.NOTICE,
        DomesticCMEFutureNoticeResponse,
    ),

    ### 국내 지수옵션 ###
    "H0IOASP0": TRMeta(
        InstrumentType.OPTION,
        MessageType.ORDERBOOK,
        DomesticIndexOptionOrderbookResponse,
    ),
    "H0IOCNT0": TRMeta(
        InstrumentType.OPTION,
        MessageType.EXECUTION,
        DomesticIndexOptionExecutionResponse,
    ), 

    ### 국내 야간옵션(EUREX) ###
    "H0EUASP0": TRMeta(
        InstrumentType.OPTION,
        MessageType.ORDERBOOK,
        DomesticEurexOptionOrderbookResponse,
    ), 
    "H0EUCNT0": TRMeta(
        InstrumentType.OPTION,
        MessageType.EXECUTION,
        DomesticEurexOptionExecutionResponse,
    ),
    "H0EUCNI0": TRMeta(
        InstrumentType.OPTION,
        MessageType.NOTICE,
        DomesticEurexOptionNoticeResponse,
    ),
}