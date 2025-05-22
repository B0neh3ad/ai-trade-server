global_broker_ws = None
active_websockets = set()

# Firebase credential, database
cred = None
db = None

# 주가 감시 설정
NOTIFICATION_EXPIRY_TIME = 30 * 60
TARGET_PRICES = list(range(340, 350, 1))