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

execution_items = [
    "종목코드", "체결시간", "현재가", "전일대비부호", "전일대비",
    "전일대비율", "가중평균가격", "시가", "최고가", "최저가",
    "매도호가1", "매수호가1", "체결거래량", "누적거래량", "누적거래대금",
    "매도체결건수", "매수체결건수", "순매수체결건수", "체결강도", "총매도수량",
    "총매수수량", "체결구분", "매수비율", "전일거래량대비등락율", "시가시간",
    "시가대비구분", "시가대비", "최고가시간", "고가대비구분", "고가대비",
    "최저가시간", "저가대비구분", "저가대비", "영업일자", "신장운영구분코드",
    "거래정지여부", "매도호가잔량", "매수호가잔량", "총매도호가잔량", "총매수호가잔량",
    "거래량회전율", "전일동시간누적거래량", "전일동시간누적거래량비율", "시간구분코드",
    "임의종료구분코드", "정적VI발동기준가"
]

orderbook_items = [
    "종목코드",
    "영업시간",
    "시간구분코드",
    "매도호가01",
    "매도호가02",
    "매도호가03",
    "매도호가04",
    "매도호가05",
    "매도호가06",
    "매도호가07",
    "매도호가08",
    "매도호가09",
    "매도호가10",
    "매수호가01",
    "매수호가02",
    "매수호가03",
    "매수호가04",
    "매수호가05",
    "매수호가06",
    "매수호가07",
    "매수호가08",
    "매수호가09",
    "매수호가10",
    "매도호가잔량01",
    "매도호가잔량02",
    "매도호가잔량03",
    "매도호가잔량04",
    "매도호가잔량05",
    "매도호가잔량06",
    "매도호가잔량07",
    "매도호가잔량08",
    "매도호가잔량09",
    "매도호가잔량10",
    "매수호가잔량01",
    "매수호가잔량02",
    "매수호가잔량03",
    "매수호가잔량04",
    "매수호가잔량05",
    "매수호가잔량06",
    "매수호가잔량07",
    "매수호가잔량08",
    "매수호가잔량09",
    "매수호가잔량10",
    "총 매도호가 잔량", # 43
    "총 매수호가 잔량",
    "시간외 총매도호가 잔량",
    "시간외 총매수호가 증감",
    "예상 체결가",
    "예상 체결량",
    "예상 거래량",
    "예상체결 대비",
    "부호",
    "예상체결 전일대비율",
    "누적거래량",
    "총 매도호가 잔량 증감",
    "총 매수호가 잔량 증감",
    "시간외 총매도호가 잔량",
    "시간외 총매수호가 증감",
    "주식매매 구분코드"
]

oversea_orderbook_items = [
    "실시간종목코드",
    "종목코드",
    "소숫점자리수",
    "현지일자",
    "현지시간",
    "한국일자",
    "한국시간",
    "총 매수호가 잔량",
    "총 매도호가 잔량",
    "총 매수호가 잔량 증감",
    "총 매도호가 잔량 증감",
    "매수호가01",
    "매도호가01",
    "매수호가잔량01",
    "매도호가잔량01",
    "매수호가잔량대비01",
    "매도호가잔량대비01",
    "매수호가02",
    "매도호가02",
    "매수호가잔량02",
    "매도호가잔량02",
    "매수호가잔량대비02",
    "매도호가잔량대비02",
    "매수호가03",
    "매도호가03",
    "매수호가잔량03",
    "매도호가잔량03",
    "매수호가잔량대비03",
    "매도호가잔량대비03",
    "매수호가04",
    "매도호가04",
    "매수호가잔량04",
    "매도호가잔량04",
    "매수호가잔량대비04",
    "매도호가잔량대비04",
    "매수호가05",
    "매도호가05",
    "매수호가잔량05",
    "매도호가잔량05",
    "매수호가잔량대비05",
    "매도호가잔량대비05",
    "매수호가06",
    "매도호가06",
    "매수호가잔량06",
    "매도호가잔량06",
    "매수호가잔량대비06",
    "매도호가잔량대비06",
    "매수호가07",
    "매도호가07",
    "매수호가잔량07",
    "매도호가잔량07",
    "매수호가잔량대비07",
    "매도호가잔량대비07",
    "매수호가08",
    "매도호가08",
    "매수호가잔량08",
    "매도호가잔량08",
    "매수호가잔량대비08",
    "매도호가잔량대비08",
    "매수호가09",
    "매도호가09",
    "매수호가잔량09",
    "매도호가잔량09",
    "매수호가잔량대비09",
    "매도호가잔량대비09",
    "매수호가10",
    "매도호가10",
    "매수호가잔량10",
    "매도호가잔량10",
    "매수호가잔량대비10",
    "매도호가잔량대비10"
]

oversea_execution_items = [
    "실시간종목코드", "종목코드", "소숫점자리수",
    "현지영업일자", "현지일자", "현지시간", "한국일자", "한국시간",
    "시가", "최고가", "최저가", "현재가", "대비구분", "전일대비", "전일대비율",
    "매수호가", "매도호가", "매수호가잔량", "매도호가잔량",
    "체결량", "거래량", "거래대금", "매도체결량", "매수체결량", "체결강도", "시장구분"
]

future_orderbook_items = [
    "종목코드",
    "영업시간",
    "매도호가01",
    "매도호가02",
    "매도호가03",
    "매도호가04",
    "매도호가05",
    "매수호가01",
    "매수호가02",
    "매수호가03",
    "매수호가04",
    "매수호가05",
    "매도호가건수01",
    "매도호가건수02",
    "매도호가건수03",
    "매도호가건수04",
    "매도호가건수05",
    "매수호가건수01",
    "매수호가건수02",
    "매수호가건수03",
    "매수호가건수04",
    "매수호가건수05",
    "매도호가잔량01",
    "매도호가잔량02",
    "매도호가잔량03",
    "매도호가잔량04",
    "매도호가잔량05",
    "매수호가잔량01",
    "매수호가잔량02",
    "매수호가잔량03",
    "매수호가잔량04",
    "매수호가잔량05",
    "총 매도호가 건수",
    "총 매수호가 건수",
    "총 매도호가 잔량",
    "총 매수호가 잔량",
    "총 매도호가 잔량 증감",
    "총 매수호가 잔량 증감"
]

notice_items = [
    "고객ID", "계좌번호", "주문번호", "원주문번호", "매도매수구분", "정정구분", "주문종류",
    "주문조건", "주식단축종목코드", "체결수량", "체결단가", "주식체결시간", "거부여부",
    "체결여부", "접수여부", "지점번호", "주문수량", "계좌명", "체결종목명", "신용구분",
    "신용대출일자", "체결종목명40", "주문가격"
]

class KoreaInvestmentPlus(mojito.KoreaInvestment):
    def __init__(self, api_key: str, api_secret: str, acc_no: str,
                 exchange: str = "서울", mock: bool = False):
        super().__init__(api_key, api_secret, acc_no, exchange, mock)

    def fetch_futureoption_price(self, market_code: str, symbol: str) -> dict:
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
        for tr_id, tr_key in zip(self.tr_id_list, self.tr_key_list):
            await self.update_subscription(True, tr_id, tr_key)

        # 체결 통보 등록
        # TODO: 국내 주식 외의 체결 통보도 등록할 수 있게 하기
        if self.user_id is not None:
            await self.update_subscription(True, "H0STCNI0", self.user_id)

        try:
            while True:
                try:
                    data = await self.websocket.recv()
                    print("[Received Data via Websocket]\n", data)
                    if data[0] == '0':
                        tokens = data.split('|')
                        ### 1-1. 국내주식 호가, 체결가, 예상체결 ###
                        if tokens[1] == "H0STASP0": # 국내주식 호가
                            self.parse_orderbook(tokens)
                        elif tokens[1] == "H0STCNT0": # 국내주식 체결
                            self.parse_execution(tokens)
                        elif tokens[1] == "H0STANC0": # 국내주식 예상체결
                            self.parse_execution(tokens)

                        ### 1-3. 국내주식 시간외 호가, 체결가, 예상체결 ###
                        elif tokens[1] == "H0STOAA0": # 국내주식 시간외호가
                            self.parse_orderbook(tokens)
                        elif tokens[1] == "H0STOUP0": # 국내주식 시간외체결
                            self.parse_execution(tokens)
                        elif tokens[1] == "H0STOAC0": # 국내주식 시간외예상체결
                            self.parse_execution(tokens)

                        ### 1-4. 국내지수 체결, 예상체결 ###
                        elif tokens[1] == "H0UPCNT0": # 국내지수 체결
                            self.parse_execution(tokens)
                        elif tokens[1] == "H0UPANC0": # 국내지수 예상체결
                            self.parse_execution(tokens)

                        ### 1-5. ELW 호가, 체결가, 예상체결 ###
                        elif tokens[1] == "H0EWASP0": # ELW 호가
                            self.parse_orderbook(tokens)
                        elif tokens[1] == "H0EWCNT0": # ELW 체결
                            self.parse_execution(tokens)
                        elif tokens[1] == "H0EWANC0": # ELW 예상체결
                            self.parse_execution(tokens)

                        ### 2-1. 해외주식 호가, 체결가 ###
                        elif tokens[1] == "HDFSASP0": # 해외주식(미국) 호가
                            self.parse_oversea_orderbook(tokens)
                        elif tokens[1] == "HDFSASP1": # 해외주식(아시아) 호가
                            self.parse_orderbook(tokens)
                        elif tokens[1] == "HDFSCNT0": # 해외주식 체결
                            self.parse_oversea_execution(tokens)

                        ### 3-1. 국내 지수선물옵션 호가, 체결가, 체결통보 ###
                        elif tokens[1] == "H0IFASP0": # 지수선물 호가
                            self.parse_orderbook(tokens)
                        elif tokens[1] == "H0IFCNT0": # 지수선물 체결
                            self.parse_execution(tokens)
                        elif tokens[1] == "H0IOASP0": # 지수옵션 호가
                            self.parse_orderbook(tokens)
                        elif tokens[1] == "H0IOCNT0": # 지수옵션 체결
                            self.parse_execution(tokens)

                        ### 3-2. 국내 상품선물 호가, 체결가 ###
                        elif tokens[1] == "H0CFASP0": # 상품선물 호가
                            self.parse_orderbook(tokens)
                        elif tokens[1] == "H0CFCNT0": # 상품선물 체결
                            self.parse_execution(tokens)

                        ### 3-3. 국내 주식선물옵션 호가, 체결가 ###
                        elif tokens[1] == "H0ZFASP0": # 주식선물 호가
                            self.parse_orderbook(tokens)
                        elif tokens[1] == "H0ZFCNT0": # 주식선물 체결
                            self.parse_execution(tokens)
                        elif tokens[1] == "H0ZFANC0": # 주식선물 예상체결
                            self.parse_execution(tokens)
                        elif tokens[1] == "H0ZOASP0": # 주식옵션 호가
                            self.parse_orderbook(tokens)
                        elif tokens[1] == "H0ZOCNT0": # 주식옵션 체결
                            self.parse_execution(tokens)
                        elif tokens[1] == "H0ZOANC0": # 주식옵션 예상체결
                            self.parse_execution(tokens)

                        ### 3-4. 국내 야간옵션(EUREX) 호가, 체결가, 예상체결 ###
                        elif tokens[1] == "H0EUASP0": # 야간옵션(EUREX) 호가
                            self.parse_orderbook(tokens)
                        elif tokens[1] == "H0EUCNT0": # 야간옵션(EUREX) 체결
                            self.parse_execution(tokens)
                        elif tokens[1] == "H0EUANC0": # 야간옵션(EUREX) 예상체결
                            self.parse_execution(tokens)

                        ### 3-5. 국내 야간선물(CME) 호가, 체결가 ###
                        elif tokens[1] == "H0MFASP0": # 야간선물(CME) 호가
                            self.parse_orderbook(tokens)
                        elif tokens[1] == "H0MFCNT0": # 야간선물(CME) 체결
                            self.parse_execution(tokens)

                        ### 4. 해외선물옵션 호가, 체결가 ###
                        elif tokens[1] == "HDFFF010": # 해외선물옵션 호가
                            self.parse_orderbook(tokens)
                        elif tokens[1] == "HDFFF020": # 해외선물옵션 체결
                            self.parse_execution(tokens)

                        ### 5. 장내채권(일반채권) 호가, 체결가 / 채권지수 체결가 ###
                        elif tokens[1] == "H0BJASP0": # 장내채권(일반채권) 호가
                            self.parse_orderbook(tokens)
                        elif tokens[1] == "H0BJCNT0": # 장내채권(일반채권) 체결
                            self.parse_execution(tokens)
                        elif tokens[1] == "H0BICNT0": # 채권지수 체결
                            self.parse_execution(tokens)
                    elif data[0] == '1':
                        tokens = data.split('|')

                        # 국내주식 체결 통보
                        if tokens[1] == "H0STCNI0" or tokens[1] == "HOSTCNI9":
                            self.parse_notice(tokens)

                        # 해외주식 체결 통보
                        elif tokens[1] == "H0GSCNI0" or tokens[1] == "H0GSCNI9":
                            self.parse_notice(tokens)

                        # 국내 지수/상품/주식 선물옵션 체결 통보
                        elif tokens[1] == "H0IFCNI0" or tokens[1] == "H0IFCNI9":
                            self.parse_notice(tokens)

                        # 야간선물옵션(CME, EUREX) 체결 통보
                        elif tokens[1] == "H0MFCNI0" or tokens[1] == "H0EUCNI0":
                            self.parse_notice(tokens)

                        # 해외선물옵션 체결 통보
                        elif tokens[1] == "HDFFF2C0":
                            self.parse_notice(tokens)
                    else:
                        ctrl_data = json.loads(data)
                        tr_id = ctrl_data["header"]["tr_id"]

                        if tr_id != "PINGPONG":
                            rt_cd = ctrl_data["body"]["rt_cd"]
                            if rt_cd == '1':  # 에러일 경우 처리
                                break
                            elif rt_cd == '0':  # 정상일 경우 처리
                                # 체결통보 처리를 위한 AES256 KEY, IV 처리 단계

                                # 국내주식
                                if tr_id == "H0STCNI0" or tr_id == "H0STCNI9":
                                    self.aes_key = ctrl_data["body"]["output"]["key"]
                                    self.aes_iv = ctrl_data["body"]["output"]["iv"]

                                # 해외주식
                                elif tr_id == "H0GSCNI0":
                                    self.aes_key = ctrl_data["body"]["output"]["key"]
                                    self.aes_iv = ctrl_data["body"]["output"]["iv"]

                                # 지수/상품/주식 선물옵션 & 야간선물옵션
                                elif tr_id == "H0IFCNI0" or tr_id == "H0MFCNI0" or tr_id == "H0EUCNI0":
                                    self.aes_key = ctrl_data["body"]["output"]["key"]
                                    self.aes_iv = ctrl_data["body"]["output"]["iv"]

                                # 해외선물옵션
                                elif tr_id == "HDFFF2C0":
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

    def parse_notice(self, tokens: list[str]):
        """_summary_
        Args:
            notice_data (_type_): 주식 체잔 데이터
        """
        code, notice_data = tokens[1], tokens[3]

        aes_dec_str = self.aes_cbc_base64_dec(notice_data)
        tokens = aes_dec_str.split('^')
        notice_data = dict(zip(notice_items, tokens))
        self.queue.put([code, notice_data])

    def parse_execution(self, tokens: list[str]):
        """주식현재가 실시간 주식 체결가 데이터 파싱
        Args:
            count (str): the number of data
            execution_data (str): 주식 체결 데이터
        """
        code, count, execution_data = tokens[1], tokens[2], tokens[3]

        tokens = execution_data.split('^')
        items_count = len(execution_items)
        for i in range(int(count)):
            parsed_data = dict(zip(execution_items, tokens[i * items_count: (i + 1) * items_count]))
            self.queue.put([code, parsed_data])

    def parse_orderbook(self, tokens: list[str]):
        """_summary_
        Args:
            orderbook_data (str): 주식 호가 데이터
        """
        code, orderbook_data = tokens[1], tokens[3]

        recvvalue = orderbook_data.split('^')
        orderbook = dict(zip(orderbook_items, recvvalue))
        self.queue.put([code, orderbook])

    def parse_oversea_execution(self, tokens: list[str]):
        """_summary_
        Args:
            execution_data (str): 주식 체결 데이터
        """
        code, count, execution_data = tokens[1], tokens[2], tokens[3]
        
        tokens = execution_data.split('^')
        items_count = len(oversea_execution_items)
        for i in range(int(count)):
            parsed_data = dict(zip(oversea_execution_items, tokens[i * items_count: (i + 1) * items_count]))
            self.queue.put([code, parsed_data])

    def parse_oversea_orderbook(self, tokens: list[str]):
        """_summary_
        Args:
            orderbook_data (str): 주식 호가 데이터
        """
        code, orderbook_data = tokens[1], tokens[3]

        recvvalue = orderbook_data.split('^')
        orderbook = dict(zip(oversea_orderbook_items, recvvalue))
        self.queue.put([code, orderbook])

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
