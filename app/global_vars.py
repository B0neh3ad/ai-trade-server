import base64
import os
from firebase_admin import credentials, firestore

from app.config import APP_KEY, APP_SECRET
from app.brokers.KoreaInvestment.main import KoreaInvestmentWSPlus

cred = None
db = None
broker_ws = None

def write_service_account_file(file_path: str = "/etc/secrets/service-account.json"):
    encoded = os.getenv("SERVICE_ACCOUNT_JSON_BASE64")
    if not encoded:
        raise RuntimeError("SERVICE_ACCOUNT_JSON_BASE64 environment variable is not set")
    json_str = base64.b64decode(encoded).decode()
    with open(file_path, "w") as f:
        f.write(json_str)

def create_broker_ws(code_list: list = None, user_id: str = None):
    broker_ws = KoreaInvestmentWSPlus(
        api_key=APP_KEY,
        api_secret=APP_SECRET,
        code_list=code_list,
        user_id=user_id  # 체결통보용 htsid
    )
    return broker_ws

def get_cred():
    global cred
    if cred is None:
        cred_path = "/etc/secrets/service-account.json"
        if not os.path.exists(cred_path):
            write_service_account_file(cred_path)
        cred = credentials.Certificate(cred_path)
    return cred

def get_db():
    global db
    if db is None:
        db = firestore.client()
    return db

def get_broker_ws():
    global broker_ws
    if broker_ws is None:
        broker_ws = create_broker_ws()
    return broker_ws