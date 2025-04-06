from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.trend import SMAIndicator
import pandas as pd


def get_rsi(close):
    rsi = RSIIndicator(pd.Series(close)).rsi()
    sma = SMAIndicator(rsi, window=14).sma_indicator()
    return rsi.tolist(), sma.tolist()


def get_macd(close):
    macd = MACD(pd.Series(close))
    return macd.macd().tolist(), macd.macd_signal().tolist(), macd.macd_diff().tolist()


def get_sma(close, window=200):
    sma = SMAIndicator(pd.Series(close), window=window).sma_indicator()
    return sma.tolist()


def get_technicals(close):
    bullish = True
    rsi, rsi_sma = get_rsi(close)
    if rsi[-1] > 70.0 or rsi_sma[-1] > 70.0:
        bullish = False

    macd, macd_signal, macd_diff = get_macd(close)
    if macd_diff[-1] < 0.0 or macd_diff[-1] < macd_diff[-2]:
        bullish = False

    return bullish, rsi, rsi_sma, macd, macd_signal, macd_diff
