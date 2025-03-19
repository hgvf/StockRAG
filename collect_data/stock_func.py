import time
from datetime import datetime

import numpy as np
import pandas as pd
import requests


def MA(df: pd.DataFrame, n: int):
    """
    Calcualte the moving average

    Parameters:
    - df (pd.DataFrame): Pandas DataFrame containing daily stock prices (e.g., closing prices).
    - n (int): Lookback period for calculating the indicator.

    Returns:
    - The calculated moving average (np.ndarray).
    """

    return df["close"].rolling(n).mean().fillna(0).to_numpy()


def KD(df: pd.DataFrame, n: int):
    """
    Calculate the KD (Stochastic Oscillator) indicator using daily stock prices.

    Parameters:
    - df (pd.DataFrame): Pandas DataFrame containing daily stock prices (e.g., closing prices).
    - n (int): Lookback period for calculating the indicator.

    Returns:
    - Pandas DataFrame with columns 'K' and 'D' representing the calculated KD values.
    """

    # Calculate RSV
    # (今日收盤價 – 最近n天的最低價) ÷ (最近n天的最高價 – 最近n天最低價) × 100
    df["Lowest Low"] = df["close"].rolling(window=n).min()
    df["Highest High"] = df["close"].rolling(window=n).max()
    df[f"RSV{n}"] = (
        100 * (df["close"] - df["Lowest Low"]) / (df["Highest High"] - df["Lowest Low"])
    )
    df = df.fillna(0)
    # ------------------------------------------------------------------------ #
    # Calculate K
    # 昨日K值 × (2/3) +今日RSV × (1/3)

    # K value in the first n days
    k1 = []
    for i in range(8):
        a = df[f"RSV{n}"].iloc[i] * (1 / 3)
        k1.append(a)

    # K value after n days
    k2 = []
    k_temp = a
    for i in range(len(df) - 8):
        k_temp = k_temp * 2 / 3 + df[f"RSV{n}"].iloc[i + 8] * (1 / 3)
        k2.append(k_temp)

    df[f"K{n}"] = pd.Series(k1 + k2)
    # ------------------------------------------------------------------------ #
    # # Calculate K
    # 今日D值 = 昨日D值 × (2/3) +今日K值 × ( 1/3)
    # D value in the first n days
    d1 = []
    for i in range(8):
        a = df[f"K{n}"].iloc[i] * (1 / 3)
        d1.append(a)

    # D value after n days
    d2 = []
    d_temp = a
    for i in range(len(df) - 8):
        d_temp = d_temp * 2 / 3 + df[f"K{n}"].iloc[i + 8] * (1 / 3)
        d2.append(d_temp)

    df[f"D{n}"] = pd.Series(d1 + d2)

    return df[[f"K{n}", f"D{n}"]].fillna(0)


def MACD(df: pd.DataFrame):
    """
    Calculate the MACD, DIF, and the histrogram between MACD and DIF

    Parameters:
    - df (pd.DataFrame): Pandas DataFrame containing daily stock prices (e.g., closing prices).

    Returns:
    - Pandas DataFrame with columns 'DIF', 'MACD' and 'histogram' representing the calculated DIF, MACD and the histogram values.
    """
    df["EMA12"] = df["close"].ewm(span=12).mean()
    df["EMA26"] = df["close"].ewm(span=26).mean()

    df["DIF"] = df["EMA12"] - df["EMA26"]
    df["MACD"] = df["DIF"].rolling(9).mean().fillna(0)
    df["histrogram"] = df["DIF"] - df["MACD"]

    return df[["DIF", "MACD", "histrogram"]]


def RSI(df: pd.DataFrame, n: int):
    """
    Calculate RSI

    Parameters:
    - df (pd.DataFrame): Pandas DataFrame containing daily stock prices (e.g., closing prices).
    - n (int): Lookback period for calculating the indicator.

    Returns:
    - The calculated RSI (np.ndarray).
    """
    delta = df["spread"]

    # 計算RSI值
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=n).mean()
    avg_loss = loss.rolling(window=n).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.fillna(0).to_numpy()
