import argparse
import time
from datetime import datetime

import pandas as pd
import psycopg2
import requests
from logger import setLogger
from stock_func import KD, MACD


def parse_args(logger):
    """
    User defined arguments
    """

    parser = argparse.ArgumentParser()

    # training hyperparameters
    parser.add_argument("--start_date", type=str, help="格式: YYYY-MM-dd")
    parser.add_argument("--subset", type=str, help="台股、美股")
    parser.add_argument(
        "--timeout", type=int, default=550, help="FinMind 每小時可以傳送的 request 數量"
    )

    opt = parser.parse_args()

    assert opt.subset in ["TW", "US"], logger.debug("Subset must in ['TW', 'US'].")

    return opt


def getStockList(logger):
    """
    Collect stockList from stockList.csv
    """

    stockList = pd.read_csv("stockList.csv")
    stockList = stockList["stock_id"].tolist()

    logger.info(f"Collect stockList...[{len(stockList)}]")

    return stockList


def getTokenURL(logger):
    """
    Get FinMind's token and URL
    """

    with open("finmind_token.txt", "r") as f:
        token = f.readlines()

    url = "https://api.finmindtrade.com/api/v4/data"

    logger.info("Getting FinMind's token and URL...")

    return token, url


def convert_dateFormat(date):
    """
    轉換時間格式
    From YYYY-MM-DD to YYYYMMDD
    """

    return f"{date[:4]}{date[5:7]}{date[8:10]}"


def saveHistory(stockList, start_date, timeout, url, token, conn, cur, subset, logger):
    """
    保存符合 event-triggered 條件的線圖，保存至 DB
    """

    logger.info("Start saving history to DB...")

    # end_date = today
    end_date = datetime.now().strftime("%Y-%m-%d")

    logger.info(f"Start-date: {start_date}, End-date: {end_date}")
    logger.info(f"Setting number of requests per hour of FinMind to ... {timeout}")

    # get the number of data in TW_MomentumInfo as history_id
    cur.execute("SELECT * FROM TW_MomentumInfo")
    res = cur.fetchall()
    history_id = len(res)
    logger.info(f"History ID start from ...{history_id}")

    act_time = time.time()
    cnt_prev = 0
    acc_cnt = 0
    for cnt, stock in enumerate(stockList):
        logger.info(f"Number...{cnt}")
        logger.info(f"Fetching stock -> {stock}")

        # sleep, preventing from service limit of FinMind
        if cnt >= timeout:
            logger.info("Pending for hour...")
            time.sleep(int(3600 - (time.time() - act_time)))

        # send request
        parameter = {
            "data_id": str(stock).strip(),
            "dataset": "TaiwanStockPrice",
            "start_date": start_date,
            "token": token,
            "end_date": end_date,
        }
        resp = requests.get(url, params=parameter)
        data = resp.json()
        df = pd.DataFrame(data["data"])

        # MACD
        macd = MACD(df)
        df = df.drop(columns=["EMA12", "EMA26"])

        # KD
        kd = KD(df, 9)
        df["K9"] = kd["K9"]
        df["D9"] = kd["D9"]
        df = df.drop(columns=["RSV9", "Lowest Low", "Highest High"])
        df = df.drop(columns=["Trading_money", "Trading_turnover", "spread"])

        # 計算 MACD 黃金交叉
        df["macd_gc"] = (df["DIF"].shift(1) < df["MACD"].shift(1)) & (
            df["DIF"] > df["MACD"]
        )
        df["his"] = df["histrogram"] >= 0.5

        # 計算 KD 黃金交叉
        df["kd_gc"] = (df["K9"].shift(1) < df["D9"].shift(1)) & (df["K9"] > df["D9"])

        # 計算收盤價漲幅、成交量變化幅度
        df["spread"] = df["close"].pct_change() * 100
        df["volumn_spread"] = df["Trading_Volume"].pct_change() * 100

        # event-triggered 條件
        # 1. 成交量變化幅度 > 200%
        # 2. 是否爆大量 (>400%)
        # 3. 漲幅是否超過 4%
        # 4. MACD 黃金交叉 & MACD-DIF > 0.5
        # 5. KD 黃金交叉
        df["volume_emerge"] = df["volumn_spread"] >= 200
        df["volume_emerge_large"] = df["volumn_spread"] >= 400
        df["spread_emerge"] = df["spread"] >= 4

        df[
            [
                "macd_gc",
                "his",
                "kd_gc",
                "volume_emerge",
                "spread_emerge",
                "volume_emerge_large",
            ]
        ] = df[
            [
                "macd_gc",
                "his",
                "kd_gc",
                "volume_emerge",
                "spread_emerge",
                "volume_emerge_large",
            ]
        ].astype(
            bool
        )

        momentum_indices = df[
            (
                ((df["macd_gc"] & df["his"]) | df["kd_gc"])
                & ((df["volume_emerge"]) | (df["spread_emerge"]))
            )
            | (df["volume_emerge_large"])
        ].index

        # 建立新的 DataFrame 來存放黃金交叉的時間點
        m_df = df.loc[
            momentum_indices,
            [
                "date",
                "stock_id",
                "close",
                "Trading_Volume",
                "macd_gc",
                "his",
                "kd_gc",
                "volume_emerge",
                "spread_emerge",
                "volume_emerge_large",
            ],
        ]

        # 存進 DB
        cnt_prev = SaveToDB(df, m_df, conn, cur, subset, history_id, acc_cnt, logger)
        acc_cnt += cnt_prev


def SaveToDB(df, m_df, conn, cur, subset, history_id, acc_cnt, logger):
    """
    把符合條件的 row 存進 DB
    """

    cnt = 0
    for idx, row in m_df.iterrows():
        h_idx = history_id + cnt + acc_cnt + 1
        print(history_id, cnt, acc_cnt)
        logger.info(f"Saving history_id: {h_idx}")

        start = row.name - 3 if row.name - 3 >= 0 else 0
        end = row.name + 40 if row.name + 40 < len(df) else len(df) - 1

        start_date = df.iloc[start]["date"]
        end_date = df.iloc[end]["date"]
        cur_price = df.iloc[start : end + 1]["close"].tolist()
        cur_vol = df.iloc[start : end + 1]["Trading_Volume"].tolist()
        cur_vol = [i / 1000 for i in cur_vol]
        cur_skillMetric = f"{str(row['macd_gc'])}, {str(row['his'])}, {str(row['kd_gc'])}, {str(row['volume_emerge'])}, {str(row['spread_emerge'])}, {str(row['volume_emerge_large'])}"
        cur_skillMetric = "{" + cur_skillMetric + "}"

        logger.info("=-" * 60)
        logger.info("Saving data: ")
        logger.info(f"\t\tStock: {row['stock_id']}")
        logger.info(f"\t\tTime interval: {start_date}-{end_date}")

        toInsert1 = (row["stock_id"], start_date, end_date, subset)

        toInsert2 = (h_idx, cur_price, cur_vol, cur_skillMetric)
        toInsert3 = (
            row["stock_id"],
            h_idx,
            f"{convert_dateFormat(start_date)}-{convert_dateFormat(end_date)}",
        )

        # insert to TW_HistoryLog
        sql = """
            INSERT INTO TW_HistoryLog (
                StockID,
                StartDate,
                EndDate,
                Category
            )
            VALUES (%s, %s, %s, %s)
        """
        try:
            cur.execute(sql, toInsert1)
            conn.commit()
        except Exception as e:
            logger.debug(f"Exception: {e}")
            conn.commit()
            continue

        # insert to TW_MomentumInfo
        sql = """
            INSERT INTO TW_MomentumInfo (
                HistoryID,
                Price,
                Volume,
                SkillMetric
            )
            VALUES (%s, %s, %s, %s)
        """
        try:
            cur.execute(sql, toInsert2)
            conn.commit()
        except Exception as e:
            logger.debug(f"Exception: {e}")
            conn.commit()
            continue

        # insert to TW_MomentumInfo
        sql = """
            INSERT INTO TW_MomentumDataHistory (
                StockID,
                HistoryID,
                TimeInterval
            )
            VALUES (%s, %s, %s)
        """
        try:
            cur.execute(sql, toInsert3)
            conn.commit()
        except Exception as e:
            logger.debug(f"Exception: {e}")
            conn.commit()
            continue

        cnt += 1

    return cnt


def loadDB(logger):
    """
    Create a connection to PostgreSQL
    """

    # connect to DB
    conn = psycopg2.connect(
        dbname="stock_db", user="weiwei", password="weiwei", host="db", port="5432"
    )
    cur = conn.cursor()

    logger.info("Connecting to PostgreSQL...")

    return conn, cur


def main():
    logger = setLogger(opt.subset)

    opt = parse_args(logger)

    stockList = getStockList(logger)

    conn, cur = loadDB(logger)
    token, url = getTokenURL(logger)

    saveHistory(
        stockList,
        opt.start_date,
        opt.timeout,
        url,
        token,
        conn,
        cur,
        opt.subset,
        logger,
    )


if __name__ == "__main__":
    main()
