import psycopg2
import requests
import pandas as pd
from datetime import datetime, timedelta

def get_query(query_stockID, flag):
    # get token and url
    with open("./collect_data/finmind_token.txt", "r") as f:
        token = f.readlines()

    url = "https://api.finmindtrade.com/api/v4/data"

    # 爬取 "query_stockID" 最近 44 個交易日相關股價
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")

    parameter = {
        "data_id": str(query_stockID).strip(),
        "dataset": "TaiwanStockPrice",
        "start_date": start_date,
        "token": token,
        "end_date": end_date,
    }
    resp = requests.get(url, params=parameter)
    data = resp.json()
    try:
        df = pd.DataFrame(data["data"])
    except Exception as e:
        return f"Exception: {e}"

    # generate queries
    query_close, query_volume = None, None
    if flag == "price":
        query_close = df['close'].tolist()[-44:]
        query_close = f"[{','.join(map(str, query_close))}]"
    else:
        query_volume = df['Trading_Volume'].tolist()[-44:]
        query_volume = [i / 1000 for i in query_volume]
        query_volume = f"[{','.join(map(str, query_volume))}]"

    return query_close, query_volume

def collect_output(price_res, vol_res, cur, flag):
    # 取得該筆歷史的 stockID, time interval, event-trigger

    price_output = []
    vol_output = []
    
    # Price
    if flag == 'price':
        for r in price_res:
            cur_output = []
            cur.execute(f"""
                    SELECT *
                    FROM TW_MomentumDataHistory
                    WHERE HistoryID = '{r[0]}';
            """)
            res = cur.fetchall()
            cur_output.append(res[0][0]) # stockID
            cur_output.append(res[0][-1]) # time interval
            
            price_output.append(cur_output)
    # Volume
    else:
        for r in vol_res:
            cur_output = []
            cur.execute(f"""
                    SELECT *
                    FROM TW_MomentumDataHistory
                    WHERE HistoryID = '{r[0]}';
            """)
            res = cur.fetchall()
            cur_output.append(res[0][0]) # stockID
            cur_output.append(res[0][-1]) # time interval
            
            vol_output.append(cur_output)

    return price_output, vol_output

def exe_SQL(cur, query_close, query_volume, flag):
    price_res, vol_res = None, None

    if flag == 'price':
        # 執行查詢 (收盤價)
        query_sql = """
            WITH candidates AS (
                SELECT HistoryID, Price
                FROM TW_Momentum
                ORDER BY Price <-> %s::vector
                LIMIT 100
            )
            SELECT HistoryID, dtw_distance(Price::vector, %s::vector) AS distance
            FROM candidates
            ORDER BY distance ASC
            LIMIT 5;
        """

        cur.execute(query_sql, (query_close, query_close))

        # 獲取結果
        price_res = cur.fetchall()
    
    else:
        # 執行查詢 (成交量)
        query_sql = """
            WITH candidates AS (
                SELECT HistoryID, Volume
                FROM TW_Momentum
                ORDER BY Volume <-> %s::vector
                LIMIT 100
            )
            SELECT HistoryID, dtw_distance(Volume::vector, %s::vector) AS distance
            FROM candidates
            ORDER BY distance ASC
            LIMIT 5;
        """

        cur.execute(query_sql, (query_volume, query_volume))

        # 獲取結果
        vol_res = cur.fetchall()

    return price_res, vol_res

def parse_output(price_output, vol_output, flag):
    out_str = ""
    # print(price_output)
    if flag == 'price':
        out_str += "以股價來說，最相似的三個線圖依序如下\n\n"
        for p in price_output:
            out_str += f"個股: {p[0]}, 時間區間: {p[-1]}\n\n"

    else:
        out_str += "以成交量來說，最相似的三個線圖依序如下\n\n"
        for p in vol_output:
            out_str += f"個股: {p[0]}, 時間區間: {p[-1]}\n\n"

    return out_str

def query_sim(query_stockID, flag):
    # connect to DB
    conn = psycopg2.connect(
        dbname="stock_db",
        user="weiwei",
        password="weiwei",
        host="db",
        port="5432"
    )
    cur = conn.cursor()

    # 設置 IVFFlat 參數
    cur.execute("SET ivfflat.probes = 10;")

    # get queries
    query_close, query_volume = get_query(query_stockID, flag)

    # 執行 SQL 取得 similar trend
    price_res, vol_res = exe_SQL(cur, query_close, query_volume, flag)
    
    # 蒐集要回傳的資料
    price_output, vol_output = collect_output(price_res, vol_res, cur, flag)

    return parse_output(price_output, vol_output, flag)