# ai-trade-server

## 환경 설정
> 아래 설명은 [python](https://www.python.org/downloads/)이 설치되어 있다는 가정 하에 진행됩니다.

1. 로컬 환경에 본 repository를 clone 합니다. 만약 git이 설치되지 않은 경우, 우선 [git을 설치](https://git-scm.com/book/ko/v2/%EC%8B%9C%EC%9E%91%ED%95%98%EA%B8%B0-Git-%EC%84%A4%EC%B9%98)합니다.
```shell
# Linux / Windows 공통
git clone https://github.com/B0neh3ad/ai-trade-server
cd ai-trade-server
```

2. 프로젝트의 최상위 디렉토리 바로 아래에 `.env` 파일을 생성한 뒤, 아래 내용을 적습니다.
```shell
# ai-trade-server/.env
APP_KEY = {한국투자증권 Open API의 app key}
APP_SECRET = {한국투자증권 Open API의 app secret}
ACC_NO = {한국투자증권 계좌번호}

TELEGRAM_BOT_TOKEN = {텔레그램 알림 봇의 token 값}
TELEGRAM_CHAT_ID = {텔레그램 테스트 유저의 chat id}
```

3. python 가상환경을 활성화한 뒤, 실행에 필요한 python 패키지들을 설치합니다.

```shell
# Linux / Windows 공통
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. 서버를 돌립니다.
```shell
fastapi dev main.py
# 또는 "sh run.sh"
```

외부에서 서버에 접속하고 싶은 경우, 포트포워딩 등 별도의 설정이 필요합니다.
테스트/디버깅을 위한 것이다면 [ngrok을 설치](https://ngrok.com/downloads/linux)한 후 아래의 명령어를 cmd(또는 terminal)에 입력합니다.
```
ngrok http 8000
```

## Data flow
아래 순서대로 각 요소를 거치며 broker -> server -> client로 데이터가 전달됩니다.

1. backend `api/broker`: 증권사 api와의 연결, 데이터 송수신을 직접 관리하는 class가 정의되어 있습니다.
2. backend `api/rest`, `api/websocket`: broker 객체의 생성 및 이를 이용한 데이터 송수신 로직을 제공합니다.
3. backend `routers`: API endpoint와 `api/rest`, `api/websocket` 내 함수들을 적절히 대응시킵니다.
---
4. frontend `lib/api`: Next.js의 각 component가 backend API를 호출할 수 있게 해주는 연결점 역할을 합니다.
5. frontend `components`: `lib/api` 의 함수들을 이용해 적절한 데이터로 UI를 구성합니다.

## (한국투자증권 API) websocket `[tr_type, tr_id, tr_key]` 예제 정리
```python
### 1-1. 국내주식 호가, 체결가, 예상체결, 체결통보 ###
# 모의투자 국내주식 체결통보: H0STCNI9
code_list = [['1','H0STASP0','005930'],['1','H0STCNT0','005930'],['1', 'H0STANC0', '005930'],['1','H0STCNI0','HTS ID를 입력하세요']]

### 1-2. 국내주식 실시간회원사, 실시간프로그램매매, 장운영정보 ###
code_list = [['1', 'H0STMBC0', '005930'], ['1', 'H0STPGM0', '005930'], ['1', 'H0STMKO0', '005930']]

### 1-3. 국내주식 시간외 호가, 체결가, 예상체결 ###
code_list = [['1','H0STOAA0','005930'],['1','H0STOUP0','005930'],['1', 'H0STOAC0', '005930']]

### 1-4. 국내지수 체결, 예상체결, 실시간프로그램매매 ###
code_list = [['1', 'H0UPCNT0', '0001'], ['1', 'H0UPANC0', '0001'], ['1', 'H0UPPGM0', '0001']]

### 1-5. ELW 호가, 체결가, 예상체결 ###
code_list = [['1', 'H0EWASP0', '58J297'],['1', 'H0EWCNT0', '58J297'],['1', 'H0EWANC0', '58J297']]

### 1-6. 국내ETF NAV 추이 ###
code_list = [['1', 'H0STNAV0', '069500']]

### 2-1. 해외주식(미국) 호가, 체결가, 체결통보 ###
# 모의투자 해외주식 체결통보: H0GSCNI9
code_list = [['1','HDFSASP0','DNASAAPL'],['1','HDFSCNT0','DNASAAPL'],['1','H0GSCNI0','HTS ID를 입력하세요']]

### 2-2. 해외주식(미국-주간) 호가, 체결가, 체결통보 ###
# 모의투자 해외주식 체결통보: H0GSCNI9
code_list = [['1','HDFSASP0','RBAQAAPL'],['1','HDFSCNT0','RBAQAAPL'],['1','H0GSCNI0','HTS ID를 입력하세요']]

### 2-3. 해외주식(아시아) 호가, 체결가, 체결통보 ###
code_list = [['1','HDFSASP1','DHKS00003'],['1','HDFSCNT0','DHKS00003'],['1','H0GSCNI0','HTS ID를 입력하세요']]

### 3-1. 국내 지수선물옵션 호가, 체결가, 체결통보 ###
# # 모의투자 선물옵션 체결통보: H0IFCNI9
code_list = [['1','H0IFASP0','101W09'],['1','H0IFCNT0','101W09']] # 지수선물호가, 체결가
                ['1','H0IOASP0','201T11317'],['1','H0IOCNT0','201T11317']] # 지수옵션호가, 체결가
                ['1','H0IFCNI0','HTS ID를 입력하세요']] # 선물옵션체결통보

### 3-2. 국내 상품선물 호가, 체결가, 체결통보 ###
code_list = [['1','H0CFASP0','175T11'],['1','H0CFCNT0','175T11'], # 상품선물호가, 체결가
              ['1','H0IFCNI0','HTS ID를 입력하세요']] # 선물옵션체결통보

### 3-3. 국내 주식선물옵션 호가, 체결가, 체결통보 ###
code_list = [['1', 'H0ZFCNT0', '111V06'], ['1', 'H0ZFASP0', '111V06'],['1', 'H0ZFANC0', '111V06'], # 주식선물호가, 체결가, 예상체결
             ['1', 'H0ZOCNT0', '211V05059'], ['1', 'H0ZOASP0', '211V05059'], ['1', 'H0ZOANC0', '211V05059'], # 주식옵션호가, 체결가, 예상체결
             ['1','H0IFCNI0','HTS ID를 입력하세요']] # 선물옵션체결통보

### 3-4. 국내 야간옵션(EUREX) 호가, 체결가, 예상체결, 체결통보 ###
code_list = [['1', 'H0EUASP0', '101W09'], ['1', 'H0EUCNT0', '101W09'], ['1', 'H0EUANC0', '101W09']]#, ['1', 'H0EUCNI0', 'HTS ID를 입력하세요']]

### 3-5. 국내 야간선물(CME) 호가, 체결가, 체결통보 ###
code_list = [['1', 'H0MFASP0', '101W09'], ['1', 'H0MFCNT0', '101W09']], ['1', 'H0MFCNI0', 'HTS ID를 입력하세요']]

### 4. 해외선물옵션 호가, 체결가, 체결통보 ###
code_list = [['1','HDFFF020','FCAZ22'],['1','HDFFF010','FCAZ22'], # 해외선물 체결가, 호가
             ['1','HDFFF020','OESH23 C3900'],['1','HDFFF010','OESH23 C3900'], # 해외옵션 체결가, 호가
             ['1','HDFFF2C0','HTS ID를 입력하세요']] # 해외선물옵션 체결통보

### 5. 장내채권(일반채권) 호가, 체결가 / 채권지수 체결가 ###
code_list = [['1','H0BJASP0','KR2033022D33'],['1','H0BJCNT0','KR2033022D33'], # 일반채권 체결가, 호가
             ['1','H0BICNT0','KBPR01']] # 채권지수 체결가
```