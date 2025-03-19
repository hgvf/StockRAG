import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from FinMind.data import DataLoader
from stock_func import *

# === TW stock selection conditions ===
# type: twse
# industry_category: all except ['ETF', 'ETN', "Index", "上櫃ETF", "上櫃指數股票型基金(ETF)", "創新板股票", "創新版股票", '受益證券', '大盤', '存託憑證', '所有證券', '指數投資證券(ETN)']
# date: 大於距目前30天前有記錄都可以

def get_token():
    with open("finmind_token.txt", "r") as f:
        token = f.readlines()
    return token

def get_allList():
    url = "https://api.finmindtrade.com/api/v4/data"
    parameter = {
        "dataset": "TaiwanStockInfo",
        "token": get_token(), # 參考登入，獲取金鑰
    }

    resp = requests.get(url, params=parameter)
    data = resp.json()
    data = pd.DataFrame(data["data"])

    return data

def filter_data(data):
    cond = np.logical_and(data['type'] == 'twse',  data['date'] >= (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    cond = np.logical_and(cond, ~data['industry_category'].isin(['ETF', 'ETN', "Index", "上櫃ETF", "上櫃指數股票型基金(ETF)", "創新板股票", "創新版股票", '受益證券', '大盤', '存託憑證', '所有證券', '指數投資證券(ETN)']))
    data = data[cond]

    return data

def main():
    data = get_allList()
    data = filter_data(data)

    data.to_csv('stockList.csv', index=False)

if __name__ == "__main__":
    main()