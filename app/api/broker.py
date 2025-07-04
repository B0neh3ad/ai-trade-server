import json
import asyncio
from base64 import b64decode
from asyncio import Queue
from typing import Dict, Set
from fastapi import WebSocket
import requests
import pandas as pd
import websockets
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

import mojito

from app.test.websocket import fake_recv
from app.utils.parser.websocket.map import TR_ID_MAP, MessageType

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

    async def ws_client(self):
        self.approval_key = self.get_approval()
        self.websocket = await websockets.connect(self.base_ws_url, ping_interval=None)
        if self.websocket is None or self.approval_key is None:
            print("websocket 또는 approval key 초기화에 실패했습니다")
            return
        
        masterfile = pd.read_csv("/home/js1044k/ai-trade-server/app/_experiment/masterfiles/fo_idx_code_mts.csv")

        ### 주/야간 지수선물 체결가 ###
        self.code_list.append([True, "H0IFCNT0", "101W09"])
        self.code_list.append([True, "H0MFCNT0", "101W09"]) # 야간선물(CME)

        ### 주/야간 지수옵션 체결가 ###
        # 구독해야 하는 코드가 너무 많아서 `MAX SUBSCRIBE OVER` 오류 발생.
        # TODO: data 적으므로 rest api 이용 pooling으로 가야할 듯.

        # # monthly option (최근월)
        # code_list = masterfile[masterfile['단축코드'].str.startswith('201W07')]['단축코드'].tolist()
        # code_list.extend(masterfile[masterfile['단축코드'].str.startswith('301W07')]['단축코드'].tolist())
        # # monthly option (차근월)
        # code_list.extend(masterfile[masterfile['단축코드'].str.startswith('201W08')]['단축코드'].tolist())
        # code_list.extend(masterfile[masterfile['단축코드'].str.startswith('301W08')]['단축코드'].tolist())
        # # weekly option (차주 월)
        # code_list.extend(masterfile[masterfile['단축코드'].str.startswith('209E0W')]['단축코드'].tolist())
        # code_list.extend(masterfile[masterfile['단축코드'].str.startswith('309E0W')]['단축코드'].tolist())
        # # weekly option (차주 목)
        # code_list.extend(masterfile[masterfile['단축코드'].str.startswith('2AFA1W')]['단축코드'].tolist())
        # code_list.extend(masterfile[masterfile['단축코드'].str.startswith('3AFA1W')]['단축코드'].tolist())
        
        # for code in code_list:
        #     self.code_list.append([True, "H0IOCNT0", code])
        #     self.code_list.append([True, "H0EUCNT0", code]) # 야간옵션(EUREX)
        
        for is_subscribe, tr_id, tr_key in self.code_list:
            # TODO: 체결 통보 코드는 self.user_id가 None이 아닌 경우에만 등록
            await self.update_subscription(is_subscribe, tr_id, tr_key)

        try:
            while True:
                try:
                    data = await self.websocket.recv()
                    # data = await fake_recv()
                    # print("\n[Data (Broker -> Server)]")
                    # print(data)
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
                                if entry.type == MessageType.NOTICE:
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

    async def update_subscription(self, is_subscription: bool, tr_id: str, tr_key: str):
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

    async def parse(self, tokens: list[str]):
        tr_id, data = tokens[1], tokens[3]
        entry = TR_ID_MAP[tr_id]

        if entry.type == MessageType.ORDERBOOK:
            tokens = data.split('^')
            tokens = tokens[:len(entry.model.__dataclass_fields__)]
            parsed_data = entry.model(*tokens)
            tr_key = parsed_data.futs_shrn_iscd
            # print("(Parsed data)\n", [tr_id, tr_key, parsed_data])
            await self.queue.put([tr_id, tr_key, parsed_data])

        elif entry.type == MessageType.EXECUTION:
            count = tokens[2]
            tokens = data.split('^')
            items_count = len(entry.model.__dataclass_fields__)
            for i in range(int(count)):
                parsed_data = entry.model(*tokens[i * items_count: (i + 1) * items_count])
                tr_key = parsed_data.futs_shrn_iscd
                # print("(Parsed data)\n", [tr_id, tr_key, parsed_data])
                await self.queue.put([tr_id, tr_key, parsed_data])

        elif entry.type == MessageType.NOTICE:
            decoded_str = self.aes_cbc_base64_dec(data)
            tokens = decoded_str.split('^')
            parsed_data = entry.model(*tokens)
            tr_key = parsed_data.futs_shrn_iscd
            # print("(Parsed data)\n", [tr_id, tr_key, parsed_data])
            await self.queue.put([tr_id, tr_key, parsed_data])

    async def get(self):
        data = await self.queue.get()
        return data
    