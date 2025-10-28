from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.trend import SMAIndicator
from ta.volatility import AverageTrueRange
import pandas as pd
from yfinance_service import P


def get_rsi(close):
    rsi = RSIIndicator(pd.Series(close)).rsi()
    sma = SMAIndicator(rsi, window=14).sma_indicator()
    return rsi.tolist(), sma.tolist()


def get_macd(close):
    macd = MACD(pd.Series(close))
    return macd.macd().tolist(), macd.macd_signal().tolist(), macd.macd_diff().tolist()


def has_momentum(close):
    macd, macd_signal, macd_diff = get_macd(close)
    # return macd[-1] > 0.0 and macd_signal[-1] > 0.0 and macd_diff[-1] > 0.0
    return macd[-1] > 0.0 or macd_signal[-1] > 0.0 or macd_diff[-1] > 0.0


def df_has_momentum(df):
    open_momentum = has_momentum(df[P.O.value])
    high_momentum = has_momentum(df[P.H.value])
    low_momentum = has_momentum(df[P.L.value])
    close_momentum = has_momentum(df[P.C.value])
    return open_momentum or high_momentum or low_momentum or close_momentum
    # return close_momentum


def get_ema(close, window=200):
    ema = EMAIndicator(pd.Series(close), window=window).ema_indicator()
    return ema.tolist()


def get_sma(close, window=200):
    sma = SMAIndicator(pd.Series(close), window=window).sma_indicator()
    return sma.tolist()


def get_technicals(close):
    bullish = True
    rsi, rsi_sma = get_rsi(close)
    if rsi[-1] > 100.0 / 3.0 and rsi_sma[-1] > 100.0 / 3.0:
        bullish = False

    macd, macd_signal, macd_diff = get_macd(close)
    if macd_diff[-1] < 0.0 or macd_diff[-2] > macd_diff[-1]:
        bullish = False

    return bullish, rsi, rsi_sma, macd, macd_signal, macd_diff


def get_reversal_by_dataframe(df):
    return (
        df[P.H.value].iat[-2] > df[P.H.value].iat[-1]
        and df[P.L.value].iat[-2] > df[P.L.value].iat[-1]
        and df[P.O.value].iat[-1] > df[P.C.value].iat[-1]
    )


def get_reversal(highs, lows, closes, opens):
    h_today = highs[-1]
    h_yesterday = highs[-2]
    l_today = lows[-1]
    l_yesterday = lows[-2]
    c = closes[-1]
    o = opens[-1]
    if h_yesterday > h_today and l_yesterday > l_today and o > c:
        # us5l = yf.Ticker('US5L.DE').history(period='1d', interval='1d')
        # message = f"Long\nGSPC@{h_today:.2f}\nUS5L@{us5l['High'].iloc[-1]:.2f}"
        return True, h_today
    elif h_yesterday < h_today and l_yesterday < l_today and o < c:
        # us5s = yf.Ticker('US5S.DE').history(period='1d', interval='1d')
        # message = f"Long\nGSPC@{l_today:.2f}\nUS5S@{us5s['High'].iloc[-1]:.2f}"
        return False, l_today
    else:
        return None, None


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


def add_smas(df, window):
    sma_high = SMAIndicator(df[P.H.value], window=window, fillna=True)
    df[f"SMA-{window} (High)"] = sma_high.sma_indicator()

    sma_low = SMAIndicator(df[P.L.value], window=window, fillna=True)
    df[f"SMA-{window} (Low)"] = sma_low.sma_indicator()

    return df


def add_emas(df, window):
    ema_high = EMAIndicator(df[P.H.value], window=window, fillna=True)
    df[f"EMA-{window} (High)"] = ema_high.ema_indicator()

    ema_low = EMAIndicator(df[P.L.value], window=window, fillna=True)
    df[f"EMA-{window} (Low)"] = ema_low.ema_indicator()

    return df
