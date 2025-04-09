from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.trend import SMAIndicator
from ta.volatility import AverageTrueRange
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


def get_supertrend(high, low, close, window=14, multiplier=2):
    atr = AverageTrueRange(pd.Series(high), pd.Series(low), pd.Series(close), window=window).average_true_range().tolist()
    price = (high[0] + low[0]) / 2
    offset = multiplier * atr[0]
    upperband = [price + offset]
    lowerband = [price - offset]
    if close[0] < lowerband[0]:
        uptrend = False
    elif close[0] > upperband[0]:
        uptrend = True
    else:
        uptrend = None

    for i in range(len(atr)):
        price = (high[i] + low[i]) / 2
        offset = multiplier * atr[i]

        if uptrend is None:
            upperband.append(min(price + offset, upperband[-1]))
            lowerband.append(max(price - offset, lowerband[-1]))
            if close[i] < lowerband[-1]:
                uptrend = False
            if close[i] > upperband[-1]:
                uptrend = True
        elif uptrend is True:
            if close[i] < lowerband[-1]:
                uptrend = False
                upperband.append(price + offset)
                lowerband.append(None)
            else:
                lowerband.append(max(price - offset, lowerband[-1]))
                upperband.append(None)
        elif uptrend is False:
            if close[i] > upperband[-1]:
                uptrend = True
                lowerband.append(price - offset)
                upperband.append(None)
            else:
                upperband.append(min(price + offset, upperband[-1]))
                lowerband.append(None)

    return upperband, lowerband
