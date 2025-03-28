from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.trend import SMAIndicator
import pandas as pd


def calculate_rsi(close):
    rsi = RSIIndicator(pd.Series(close)).rsi()
    sma = SMAIndicator(rsi, window=14).sma_indicator()
    return rsi.tolist(), sma.tolist()


def calculate_macd(close):
    macd = MACD(pd.Series(close))
    return macd.macd().tolist(), macd.macd_signal().tolist(), macd.macd_diff().tolist()


def calculate_sma_220(close):
    sma_220 = SMAIndicator(pd.Series(close), window=220).sma_indicator()
    return sma_220.tolist()