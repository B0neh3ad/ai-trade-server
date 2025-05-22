import json
import asyncio
from base64 import b64decode
from multiprocessing import Process, Queue
import requests
import pandas as pd
import websockets
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

import mojito

from app.utils.parser.websocket.map import TR_CODE_MAP, MessageType

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
            "fid_cond_mrkt_div_code": market_code,
            "fid_input_iscd": symbol
        }
        resp = requests.get(url, headers=headers, params=params)
        return resp.json()

    def fetch_oversea_price(self, symbol: str) -> dict:
        """해외주식현재가/해외주식 현재체결가
        Args:
            symbol (str): 종목코드
        Returns:
            dict: API 개발 가이드 참조
        """
        path = "uapi/overseas-price/v1/quotations/price"
        url = f"{self.base_url}/{path}"

        # request header
        headers = {
           "content-type": "application/json",
           "authorization": self.access_token,
           "appKey": self.api_key,
           "appSecret": self.api_secret,
           "tr_id": "HHDFS00000300"
        }

        # query parameter
        try:
            exchange_code = EXCHANGE_CODE[self.exchange]
        except KeyError:
            exchange_code = EXCHANGE_CODE["나스닥"]
        params = {
            "AUTH": "",
            "EXCD": exchange_code,
            "SYMB": symbol
        }
        resp = requests.get(url, headers=headers, params=params)
        return resp.json()

class KoreaInvestmentWSPlus(Process):
    """WebSocket
    """

    def __init__(self, api_key: str, api_secret: str, tr_id_list: list,
                 tr_key_list: list, user_id: str = None):
        """_summary_
        Args:
            api_key (str): _description_
            api_secret (str): _description_
            tr_id_list (list): _description_
            tr_key_list (list): _description_
            user_id (str, optional): _description_. Defaults to None.
        """
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.tr_id_list = tr_id_list
        self.tr_key_list = tr_key_list
        self.user_id = user_id
        self.aes_key = None
        self.aes_iv = None
        self.queue = Queue()
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.base_ws_url = "ws://ops.koreainvestment.com:21000"
        self.websocket = None
        self.subscription = {}

    def run(self):
        asyncio.run(self.ws_client())

    async def ws_client(self):
        approval_key = self.get_approval()

        self.websocket = await websockets.connect(self.base_ws_url, ping_interval=None)
        # 체결, 호가 등록
        for tr_id in self.tr_id_list:
            for tr_key in self.tr_key_list:
                await self.update_subscription(True, tr_id, tr_key)

        # 체결 통보 등록
        # TODO: 국내 주식 외의 체결 통보도 등록할 수 있게 하기
        if self.user_id is not None:
            await self.update_subscription(True, "H0STCNI0", self.user_id)

        try:
            while True:
                try:
                    data = await self.websocket.recv()
                    if data[0] == '0':
                        tokens = data.split('|')
                        self.parse(tokens)

                        # ### 국내 지수선물옵션 호가, 체결가, 체결통보 ###
                        # if tokens[1] == "H0IFASP0": # 지수선물 호가
                        #     self.parse_orderbook(tokens)
                        # elif tokens[1] == "H0IFCNT0": # 지수선물 체결
                        #     self.parse_execution(tokens)

                        # ### 국내 야간선물(CME) 호가, 체결가 ###
                        # elif tokens[1] == "H0MFASP0": # 야간선물(CME) 호가
                        #     self.parse_orderbook(tokens)
                        # elif tokens[1] == "H0MFCNT0": # 야간선물(CME) 체결
                        #     self.parse_execution(tokens)

                    elif data[0] == '1':
                        tokens = data.split('|')
                        self.parse(tokens)

                        # # 국내 지수/상품/주식 선물옵션 체결 통보
                        # if tokens[1] == "H0IFCNI0" or tokens[1] == "H0IFCNI9":
                        #     self.parse_notice(tokens)

                        # # 야간선물옵션(CME, EUREX) 체결 통보
                        # elif tokens[1] == "H0MFCNI0" or tokens[1] == "H0EUCNI0":
                        #     self.parse_notice(tokens)
                    else:
                        ctrl_data = json.loads(data)
                        tr_id = ctrl_data["header"]["tr_id"]

                        if tr_id != "PINGPONG":
                            rt_cd = ctrl_data["body"]["rt_cd"]
                            if rt_cd == '1':  # 에러일 경우 처리
                                break
                            elif rt_cd == '0':  # 정상일 경우 처리
                                # 체결통보 처리를 위한 AES256 KEY, IV 처리 단계
                                entry = TR_CODE_MAP[tr_id]
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
        approval_key = self.get_approval()

        header = {
            "approval_key": approval_key,
            "personalseckey": "1",
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
            if (tr_id, tr_key) not in self.subscription:
                fmt["header"]["tr_type"] = "1"
                fmt["body"]["input"]["tr_id"] = tr_id
                fmt["body"]["input"]["tr_key"] = tr_key
                self.subscription[(tr_id, tr_key)] = 1
            else:
                self.subscription[(tr_id, tr_key)] += 1
        else:  
            if (tr_id, tr_key) not in self.subscription:
                # cannot unsubscribe unsubscribed data
                return
            elif self.subscription[(tr_id, tr_key)] == 1:
                fmt["header"]["tr_type"] = "2"
                fmt["body"]["input"]["tr_id"] = tr_id
                fmt["body"]["input"]["tr_key"] = tr_key
                del self.subscription[(tr_id, tr_key)]
            else:
                self.subscription[(tr_id, tr_key)] -= 1
        
        if fmt["body"]["input"]["tr_id"] and fmt["body"]["input"]["tr_key"]:
            subscribe_data = json.dumps(fmt)
            await self.websocket.send(subscribe_data)
            print("[Websocket 구독/구독해제 요청 완료]\n", subscribe_data)
        
        # TODO: 요청에 대한 응답을 받은 뒤에 구독 상태 update하기
        print("[현재 구독상태]\n", self.subscription)

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

    def parse(self, tokens: list[str]):
        code, data = tokens[1], tokens[3]
        entry = TR_CODE_MAP[code]

        if entry.type == MessageType.ORDERBOOK:
            tokens = data.split('^')
            parsed_data = entry.model(*tokens)
            self.queue.put([code, parsed_data])

        elif entry.type == MessageType.EXECUTION:
            count = tokens[2]
            tokens = data.split('^')
            items_count = len(entry.model.__dataclass_fields__)
            for i in range(int(count)):
                parsed_data = entry.model(*tokens[i * items_count: (i + 1) * items_count])
                self.queue.put([code, parsed_data])

        elif entry.type == MessageType.NOTICE:
            decoded_str = self.aes_cbc_base64_dec(data)
            tokens = decoded_str.split('^')
            parsed_data = entry.model(*tokens)
            self.queue.put([code, parsed_data])

    def get(self):
        """get data from the queue

        Returns:
            _type_: _description_
        """
        data = self.queue.get()
        return data

    def terminate(self):
        if self.is_alive():
            self.kill()
