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

FCM_SERVER_KEY = {firebase FCM 서버의 key}
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

## 프로젝트 구조

`main.py`: API Endpoint \
`config.py`: 환경변수 불러오기 & 설정 \
`api/api.py`: 한국투자증권 API에 대한 로컬 API 함수들 \
`api/broker.py`: 증권사 class
