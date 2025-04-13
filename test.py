import mojito
from config import APP_KEY, APP_SECRET
from api.api import KoreaInvestmentWSPlus


if __name__ == "__main__":
    broker_ws = KoreaInvestmentWSPlus(
        api_key=APP_KEY,
        api_secret=APP_SECRET,
        tr_id_list=["H0STASP0", "H0STCNT0"],
        tr_key_list=["005930", "005930"],
        user_id=None # 체결통보용 htsid
    )

    broker_ws.start()
    while True:
        data_ = broker_ws.get()
        if data_[0] == '체결':
            print(data_[1])
        elif data_[0] == '호가':
            print(data_[1])
        elif data_[0] == '체잔':
            print(data_[1])