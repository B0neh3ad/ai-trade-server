import mojito
from config import APP_KEY, APP_SECRET
from api.api import KoreaInvestmentWSPlus, fetch_domestic_stock_price, fetch_domestic_indexfuture_price


if __name__ == "__main__":
    broker_ws = KoreaInvestmentWSPlus(
        api_key=APP_KEY,
        api_secret=APP_SECRET,
        tr_id_list=["H0STASP0"],
        tr_key_list=["005930"],
        user_id=None # 체결통보용 htsid
    )

    broker_ws.start()
    while True:
        data_ = broker_ws.get()
    # write test code for fetch_domestic_futureoption_price in api.py
    # print(fetch_domestic_futureoption_price())
