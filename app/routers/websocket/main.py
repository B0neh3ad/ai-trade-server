from fastapi import APIRouter, WebSocket

from app.utils.websocket import websocket_handler

from . import domestic_futureoption, overseas_stock

router = APIRouter()

router.include_router(domestic_futureoption.router)
router.include_router(overseas_stock.router)

@router.websocket("/H0STASP0")
async def websocket_orderbook(websocket: WebSocket):
    await websocket_handler(
        websocket,
        tr_id_list=["H0STASP0"],
        tr_key_list=["005930"]
    )

@router.websocket("/H0STCNT0")
async def websocket_execution(websocket: WebSocket):
    await websocket_handler(
        websocket,
        tr_id_list=["H0STCNT0"],
        tr_key_list=["005930"]
    )

'''
<미국 야간거래/아시아 주간거래 - 무료시세>
D+시장구분(3자리)+종목코드
예) DNASAAPL : D+NAS(나스닥)+AAPL(애플)
[시장구분]
NYS : 뉴욕, NAS : 나스닥, AMS : 아멕스 ,
TSE : 도쿄, HKS : 홍콩,
SHS : 상해, SZS : 심천
HSX : 호치민, HNX : 하노이 
'''

@router.websocket("/HDFSASP0")
async def websocket_overseas_orderbook(websocket: WebSocket):
    await websocket_handler(
        websocket,
        tr_id_list=["HDFSASP0"],
        tr_key_list=["DNASAAPL"]
    )

@router.websocket("/HDFSCNT0")
async def websocket_overseas_execution(websocket: WebSocket):
    await websocket_handler(
        websocket,
        tr_id_list=["HDFSCNT0"],
        tr_key_list=["DNASAAPL"]
    )