import datetime
import json
import asyncio
from base64 import b64decode
from asyncio import Queue
from typing import Dict, List, Set
from fastapi import WebSocket
import requests
import pandas as pd
import websockets
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, time, timedelta

import mojito

from app.test.websocket import fake_recv
from app.utils.parser.websocket.map import TR_ID_MAP, InstrumentType, MessageType

EXCHANGE_CODE = {
    "홍콩": "HKS",
    "뉴욕": "NYS",
    "나스닥": "NAS",
    "아멕스": "AMS",
    "도쿄": "TSE",
    "상해": "SHS",
    "심천": "SZS",
    "상해지수": "SHI",
    "심천지수": "SZI",
    "호치민": "HSX",
    "하노이": "HNX"
}

@dataclass
class FuturesInfo:
    """선물 정보를 관리하는 데이터클래스"""
    code: str
    maturity_contract: str
    
@dataclass
class OptionsInfo:
    """옵션 정보를 관리하는 데이터클래스"""
    code: str
    min_strike: float
    max_strike: float
    market_class_code: str
    maturity_contract: str
    label: str

@dataclass
class FutureOptionInfo:
    """거래 코드 정보를 관리하는 데이터클래스"""
    futures: List[FuturesInfo]
    options: List[OptionsInfo]

class MarketStatus(Enum):
    NORMAL = 1
    NIGHT = 2
    OTHER = 0

class KoreaInvestmentPlus(mojito.KoreaInvestment):
    def __init__(self, api_key: str, api_secret: str, acc_no: str,
                 exchange: str = "서울", mock: bool = False):
        super().__init__(api_key, api_secret, acc_no, exchange, mock)

    def fetch_domestic_futureoption_price(self, market_code: str, symbol: str) -> dict:
        """선물옵션시세
        Args:
            market_code (str): 시장 분류코드
            symbol (str): 종목코드
        Returns:
            dict: API 개발 가이드 참조
        """
        path = "/uapi/domestic-futureoption/v1/quotations/inquire-price"
        url = f"{self.base_url}/{path}"
        headers = {
           "content-type": "application/json",
           "authorization": self.access_token,
           "appKey": self.api_key,
           "appSecret": self.api_secret,
           "tr_id": "FHMIF10000000"
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": market_code,
            "FID_INPUT_ISCD": symbol
        }
        resp = requests.get(url, headers=headers, params=params)
        return resp.json()

    def fetch_domestic_futureoption_asking_price(self, market_code: str, symbol: str) -> dict:
        """
            선물옵션 시세호가 조회 API
            Args:
                market_code (str): 시장 분류코드
                symbol (str): 종목코드
            Returns:
                dict: API 개발 가이드 참조
        """
        path = "/uapi/domestic-futureoption/v1/quotations/inquire-price"
        url = f"{self.base_url}/{path}"
        headers = {
           "content-type": "application/json",
           "authorization": self.access_token,
           "appKey": self.api_key,
           "appSecret": self.api_secret,
           "tr_id": "FHMIF10010000"
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": market_code,
            "FID_INPUT_ISCD": symbol
        }
        resp = requests.get(url, headers=headers, params=params)
        return resp.json()
    
    def fetch_display_board_option_list(self) -> dict:
        """옵션전광판 옵션월물리스트 조회"""
        path = "/uapi/domestic-futureoption/v1/quotations/display-board-option-list"
        url = f"{self.base_url}/{path}"
        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": "FHPIO056104C0"
        }
        params = {
            "FID_COND_SCR_DIV_CODE": "509",
            "FID_COND_MRKT_DIV_CODE": "",
            "FID_COND_MRKT_CLS_CODE": "",
        }
        resp = requests.get(url, headers=headers, params=params)
        return resp.json()

    def fetch_display_board_callput(self, market_class_code: str, maturity_contract: str) -> dict:
        """
            국내옵션전광판 콜풋 조회 API
            (KOSPI200 옵션 조회에 활용)

            주의: polling 방식으로 사용 시 1초에 최대 1건 조회 권장. (비용이 큼)

            Args:
                market_class_code (str): 시장 분류코드
                - 공백: KOSPI200
                - WKM: KOSPI200위클리(월)
                - WKI: KOSPI200위클리(목)
                
                maturity_contract (str): 만기 계약
                - FID_COND_MRKT_CLS_CODE가 공백(KOSPI200) 인 경우
                    - 만기년월(YYYYMM) 입력 (ex. 202407)
                - FID_COND_MRKT_CLS_CODE가 WKM(KOSPI200위클리(월)), WKI(KOSPI200위클리(목)) 인 경우
                    - 만기년월주차(YYMMWW) 입력 (ex. 2024년도 7월 3주차인 경우, 240703 입력)
            Returns:
                dict: API 개발 가이드 참조
        """

        path = "/uapi/domestic-futureoption/v1/quotations/display-board-callput"
        url = f"{self.base_url}/{path}"
        headers = {
            "content-type": "application/json",
            "authorization": self.access_token,
            "appKey": self.api_key,
            "appSecret": self.api_secret,
            "tr_id": "FHPIF05030100"
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "O",
            "FID_COND_SCR_DIV_CODE": "20503",
            "FID_MRKT_CLS_CODE": "CO", # 콜옵션
            "FID_MTRT_CNT": maturity_contract,
            "FID_COND_MRKT_CLS_CODE": market_class_code,
            "FID_MRKT_CLS_CODE1": "PO", # 풋옵션
        }
        resp = requests.get(url, headers=headers, params=params)
        return resp.json()

class KoreaInvestmentWSPlus:
    """WebSocket
    """

    def __init__(self, api_key: str, api_secret: str, code_list: list = None,
                 user_id: str = None):
        
        self.api_key = api_key
        self.api_secret = api_secret
        self.approval_key = None
        self.code_list = code_list if code_list is not None else []
        self.user_id = user_id
        self.aes_key = None
        self.aes_iv = None
        self.queue = Queue()
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.base_ws_url = "ws://ops.koreainvestment.com:21000"
        self.websocket = None
        self.subscribed_to_broker: Set[str] = set()
        self.option_subscriptions: Dict[str, Set[str]] = {}
        
        # 거래 코드 정보를 저장하는 멤버 변수
        self.futureoptions_info: FutureOptionInfo = None

    def init_futureoptions_info(self):
        masterfile = pd.read_csv("/home/js1044k/ai-trade-server/app/_experiment/masterfiles/fo_idx_code_mts.csv")
        masterfile.columns = masterfile.columns.str.strip()

        # 선물 정보 추출
        futures = masterfile[masterfile['한글종목명'].str.startswith('F ')]
        futures = futures.sort_values(by='한글종목명')

        recent_futures_code = futures['단축코드'][0]
        recent_futures_maturity_contract = futures['한글종목명'].iloc[0].split(' ')[1]
        next_recent_futures_code = futures['단축코드'][1]
        next_recent_futures_maturity_contract = futures['한글종목명'].iloc[1].split(' ')[1]

        # 월간 옵션 정보 추출
        monthly_options = masterfile[masterfile['한글종목명'].str.startswith('C ')].copy()
        monthly_options['한글종목명_행사가제외'] = monthly_options['한글종목명'].str.split(' ').str[:-1].str.join(' ')

        monthly_options_min = monthly_options.groupby('한글종목명_행사가제외').min()
        monthly_options_max = monthly_options.groupby('한글종목명_행사가제외').max()
        monthly_options_codes = monthly_options_min['단축코드'].iloc[0][1:-3]

        monthly_options_min_strike = float(monthly_options_min['행사가'].iloc[0])
        monthly_options_max_strike = float(monthly_options_max['행사가'].iloc[0])

        monthly_options_maturity_contract = monthly_options['한글종목명'].iloc[0].split(' ')[1].replace('M', '0')

        # 주간 옵션 정보 추출
        weekly_options = masterfile[masterfile['한글종목명'].str.startswith('위클리')].copy()
        weekly_options['한글종목명_행사가제외'] = weekly_options['한글종목명'].str.split(' ').str[:-1].str.join(' ')

        # 월요일 만기 옵션
        weekly_options_monday = weekly_options[weekly_options['한글종목명'].str.startswith('위클리C')]
        if len(weekly_options_monday) > 0:
            weekly_options_monday_code = weekly_options_monday['단축코드'].iloc[0][1:-3]
            weekly_options_monday_min_strike = float(weekly_options_monday['행사가'].min())
            weekly_options_monday_max_strike = float(weekly_options_monday['행사가'].max())
            weekly_options_monday_maturity_contract = weekly_options_monday['한글종목명'].iloc[0].split(' ')[1].replace('W', '0')
        else:
            weekly_options_monday_code = None
            weekly_options_monday_min_strike = 0
            weekly_options_monday_max_strike = 0
            weekly_options_monday_maturity_contract = None

        # 목요일 만기 옵션
        weekly_options_thursday = weekly_options[weekly_options['한글종목명'].str.startswith('위클리M')]
        if len(weekly_options_thursday) > 0:
            weekly_options_thursday_code = weekly_options_thursday['단축코드'].iloc[0][1:-3]
            weekly_options_thursday_min_strike = float(weekly_options_thursday['행사가'].min())
            weekly_options_thursday_max_strike = float(weekly_options_thursday['행사가'].max())
            weekly_options_thursday_maturity_contract = weekly_options_thursday['한글종목명'].iloc[0].split(' ')[2].replace('W', '0')
        else:
            weekly_options_thursday_code = None
            weekly_options_thursday_min_strike = 0
            weekly_options_thursday_max_strike = 0
            weekly_options_thursday_maturity_contract = None

        # 클래스 멤버 변수로 저장
        futures_info = [
            FuturesInfo(
                code=recent_futures_code,
                maturity_contract=recent_futures_maturity_contract
            ), FuturesInfo(
                code=next_recent_futures_code,
                maturity_contract=next_recent_futures_maturity_contract
            )
        ]

        monthly_options_info = OptionsInfo(
            code=monthly_options_codes,
            min_strike=monthly_options_min_strike,
            max_strike=monthly_options_max_strike,
            market_class_code="",
            maturity_contract=monthly_options_maturity_contract,
            label=f"KOSPI200 {monthly_options_maturity_contract}"
        )

        weekly_options_info = None
        if weekly_options_monday_code is not None:
            weekly_options_info = OptionsInfo(
                code=weekly_options_monday_code,
                min_strike=weekly_options_monday_min_strike,
                max_strike=weekly_options_monday_max_strike,
                market_class_code="WKM",
                maturity_contract=weekly_options_monday_maturity_contract,
                label=f"KOSPI200 위클리(월) {weekly_options_monday_maturity_contract}"
            )
        elif weekly_options_thursday_code is not None:
            weekly_options_info = OptionsInfo(
                code=weekly_options_thursday_code,
                min_strike=weekly_options_thursday_min_strike,
                max_strike=weekly_options_thursday_max_strike,
                market_class_code="WKI",
                maturity_contract=weekly_options_thursday_maturity_contract,
                label=f"KOSPI200 위클리(목) {weekly_options_thursday_maturity_contract}"
            )
        
        if weekly_options_info is not None:
            options_info = [monthly_options_info, weekly_options_info]
        else:
            options_info = [monthly_options_info]
        
        self.futureoptions_info = FutureOptionInfo(
            futures=futures_info,
            options=options_info
        )

    def get_options_info(self) -> List[OptionsInfo]:
        if self.futureoptions_info is None:
            return []
        return self.futureoptions_info.options
    
    def get_futures_info(self) -> List[FuturesInfo]:
        if self.futureoptions_info is None:
            return []
        return self.futureoptions_info.futures

    def get_market_status(self) -> MarketStatus:
        # 현재 시간을 KST 기준으로 얻기
        now_utc = datetime.utcnow()
        now_kst = now_utc + timedelta(hours=9)
        current_time = now_kst.time()

        # 시장 시간 정의
        regular_start = time(8, 45)
        regular_end = time(15, 45)

        night_start = time(18, 0)
        night_end = time(5, 0)

        if regular_start <= current_time <= regular_end:
            return MarketStatus.NORMAL
        elif current_time >= night_start or current_time <= night_end:
            return MarketStatus.NIGHT
        else:
            return MarketStatus.OTHER
        
    async def ws_client(self, print_log: bool = True):
        self.approval_key = self.get_approval()
        self.websocket = await websockets.connect(self.base_ws_url, ping_interval=None)
        if self.websocket is None or self.approval_key is None:
            print("websocket 또는 approval key 초기화에 실패했습니다")
            return
        
        # 거래 코드 정보 초기화
        self.init_futureoptions_info()
        # TODO: loop 내에서 market_status 지속적으로 확인 & 구독 정보 update 필요
        market_status = self.get_market_status()
        
        if market_status == MarketStatus.OTHER:
            print("현재는 장외 시간입니다.")
            return

        if market_status == MarketStatus.NORMAL:
            future_orderbook = "H0IFASP0"
            future_execution = "H0IFCNT0"
            option_execution = "H0IOCNT0"
        else:
            future_orderbook = "H0MFASP0"
            future_execution = "H0MFCNT0"
            option_execution = "H0EUCNT0"

        ### 지수선물 호가, 체결가 ###
        for future in self.futureoptions_info.futures:
            self.code_list.append([True, future_orderbook, future.code])
            self.code_list.append([True, future_execution, future.code])

        for is_subscribe, tr_id, tr_key in self.code_list:
            # TODO: 체결 통보 코드는 self.user_id가 None이 아닌 경우에만 등록
            await self.update_subscription(is_subscribe, tr_id, tr_key)

        ### 지수옵션 체결가 ###
        option_codes = [options.code for options in self.futureoptions_info.options]
        for code in option_codes:
            self.code_list.append([True, option_execution, code])

        try:
            while True:
                try:
                    data = await self.websocket.recv()
                    # data = await fake_recv() # 테스트용
                    if print_log:
                        print("\n[Data (Broker -> Server)]")
                        print(data)
                    if data[0] in ['0', '1']:
                        # 호가, 체결, 체결통보 중 하나인 경우
                        tokens = data.split('|')
                        await self.parse(tokens)
                    else:
                        ctrl_data = json.loads(data)
                        tr_id = ctrl_data["header"]["tr_id"]

                        if tr_id != "PINGPONG":
                            rt_cd = ctrl_data["body"]["rt_cd"]
                            if rt_cd == '1':  # 에러일 경우 처리
                                break
                            elif rt_cd == '0':  # 정상일 경우 처리
                                # 체결통보 처리를 위한 AES256 KEY, IV 처리 단계
                                entry = TR_ID_MAP[tr_id]
                                if entry.message_type == MessageType.NOTICE:
                                    self.aes_key = ctrl_data["body"]["output"]["key"]
                                    self.aes_iv = ctrl_data["body"]["output"]["iv"]

                        elif tr_id == "PINGPONG":
                            await self.websocket.send(data)
                except websockets.exceptions.ConnectionClosedOK:
                    print("✅ 웹소켓 정상 종료")
                    break
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"⚠️ 웹소켓 연결 오류 (close frame 없음): {e}")
                    try:
                        # close frame 전송 시도
                        await self.websocket.close(code=1000, reason="Sending close frame manually")
                        print("✅ 직접 close frame 전송 완료")
                    except Exception as err:
                        print(f"❗ close frame 전송 중 오류: {err}")
                    break
                except Exception as e:
                    print(f"⚠️ 데이터 처리 중 에러: {e}")
                    continue
        except Exception as e:
            print(f"가격 감시 중 오류 발생: {e}")

    async def update_subscription(self, is_subscription: bool, tr_id: str, tr_key: str, print_log: bool = False):
        if self.websocket is None or self.approval_key is None:
            return
        
        header = {
            "approval_key": self.approval_key,
            "custtype": "P",
            "tr_type": "1",
            "content-type": "utf-8"
        }
        fmt = {
            "header": header,
            "body": {
                "input": {
                    "tr_id": None,
                    "tr_key": None,
                }
            }
        }

        if is_subscription:
            if f"{tr_id}:{tr_key}" not in self.subscribed_to_broker:
                fmt["header"]["tr_type"] = "1"
                fmt["body"]["input"]["tr_id"] = tr_id
                fmt["body"]["input"]["tr_key"] = tr_key
                self.subscribed_to_broker.add(f"{tr_id}:{tr_key}")
        else:
            if f"{tr_id}:{tr_key}" in self.subscribed_to_broker:
                fmt["header"]["tr_type"] = "2"
                fmt["body"]["input"]["tr_id"] = tr_id
                fmt["body"]["input"]["tr_key"] = tr_key
                self.subscribed_to_broker.remove(f"{tr_id}:{tr_key}")
        
        if fmt["body"]["input"]["tr_id"] and fmt["body"]["input"]["tr_key"]:
            subscribe_data = json.dumps(fmt)
            if print_log:
                print("\n[Subscribe Request (Server -> Broker)]")
                print(subscribe_data)
            try:
                await self.websocket.send(subscribe_data)
            except websockets.exceptions.ConnectionClosedOK:
                print("⚠️ 웹소켓 연결이 끊어졌습니다. 다시 연결합니다.")
                await self.ws_client()
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"⚠️ 웹소켓 연결 오류 (close frame 없음): {e}")
                try:
                    # close frame 전송 시도
                    await self.websocket.close(code=1000, reason="Sending close frame manually")
                    print("✅ 직접 close frame 전송 완료")
                except Exception as err:
                    print(f"❗ close frame 전송 중 오류: {err}")
            except Exception as e:
                print(f"⚠️ 웹소켓 구독/구독해제 요청 중 오류: {e}")

    async def update_option_subscriptions(self, tr_key: str, new_option_codes: Set[str]):
        if tr_key not in self.option_subscriptions:
            self.option_subscriptions[tr_key] = set()

        market_status = self.get_market_status()
        if market_status == MarketStatus.OTHER:
            return
        
        to_subscribe = new_option_codes - self.option_subscriptions[tr_key]
        to_unsubscribe = self.option_subscriptions[tr_key] - new_option_codes

        if market_status == MarketStatus.NORMAL:
            option_execution = "H0IOCNT0"
        else:
            option_execution = "H0EUCNT0"

        # 옵션 체결 구독 업데이트
        for code in to_unsubscribe:
            await self.update_subscription(False, option_execution, code)
        
        for code in to_subscribe:
            await self.update_subscription(True, option_execution, code)

        self.option_subscriptions[tr_key] = new_option_codes

    def get_approval(self) -> str:
        """실시간 (웹소켓) 접속키 발급

        Returns:
            str: 웹소켓 접속키
        """
        headers = {"content-type": "application/json"}
        body = {"grant_type": "client_credentials",
                "appkey": self.api_key,
                "secretkey": self.api_secret}
        PATH = "oauth2/Approval"
        URL = f"{self.base_url}/{PATH}"
        res = requests.post(URL, headers=headers, data=json.dumps(body))
        return res.json()["approval_key"]

    def aes_cbc_base64_dec(self, cipher_text: str):
        """_summary_
        Args:
            cipher_text (str): _description_
        Returns:
            _type_: _description_
        """
        cipher = AES.new(self.aes_key.encode('utf-8'), AES.MODE_CBC, self.aes_iv.encode('utf-8'))
        return bytes.decode(unpad(cipher.decrypt(b64decode(cipher_text)), AES.block_size))

    async def parse(self, tokens: list[str], print_log: bool = False):
        tr_id, data = tokens[1], tokens[3]
        entry = TR_ID_MAP[tr_id]

        if entry.message_type == MessageType.ORDERBOOK:
            tokens = data.split('^')
            tokens = tokens[:len(entry.model.__dataclass_fields__)]
            parsed_data = entry.model(*tokens)
            tr_key = parsed_data.shrn_iscd
            if entry.instrument_type == InstrumentType.OPTION:
                tr_key = tr_key[1:-3]
            if print_log:
                print("(Parsed data)\n", [tr_id, tr_key, parsed_data])
            await self.queue.put([tr_id, tr_key, parsed_data])

        elif entry.message_type == MessageType.EXECUTION:
            count = tokens[2]
            tokens = data.split('^')
            items_count = len(entry.model.__dataclass_fields__)
            for i in range(int(count)):
                parsed_data = entry.model(*tokens[i * items_count: (i + 1) * items_count])
                tr_key = parsed_data.shrn_iscd
                if entry.instrument_type == InstrumentType.OPTION:
                    tr_key = tr_key[1:-3]
                if print_log:
                    print("(Parsed data)\n", [tr_id, tr_key, parsed_data])
                await self.queue.put([tr_id, tr_key, parsed_data])

        elif entry.message_type == MessageType.NOTICE:
            decoded_str = self.aes_cbc_base64_dec(data)
            tokens = decoded_str.split('^')
            parsed_data = entry.model(*tokens)
            tr_key = parsed_data.shrn_iscd
            if entry.instrument_type == InstrumentType.OPTION:
                tr_key = tr_key[1:-3]
            if print_log:
                print("(Parsed data)\n", [tr_id, tr_key, parsed_data])
            await self.queue.put([tr_id, tr_key, parsed_data])

    async def get(self):
        data = await self.queue.get()
        return data
    