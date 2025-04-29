import enum
from enum import Enum

import pandas as pd
import yfinance as yf
import math


class P(Enum):
    O = 'Open'
    H = 'High'
    L = 'Low'
    C = 'Close'


def get_price(ticker, period='1d', interval='1m'):
    data = yf.Ticker(ticker).history(period=period, interval=interval)
    return data["Close"].iloc[-1]


def get_high_low(ticker, period='1d', interval='1m'):
    data = yf.Ticker(ticker).history(period=period, interval=interval)
    return data["High"].iloc[-1], data["Low"].iloc[-1]


def get_high_low_close(ticker, period='1y', interval='1d'):
    highs, lows, closes, opens = get_prices([ticker], period=period, interval=interval)
    return highs[ticker], lows[ticker], closes[ticker]


def get_prices(tickers, period='10y', interval='1d'):
    data = yf.download(tickers=tickers, period=period, interval=interval)
    highs = {}
    lows = {}
    closes = {}
    opens = {}
    high_all = data["High"]
    low_all = data["Low"]
    close_all = data["Close"]
    open_all = data["Open"]
    for ticker in tickers:
        highs[ticker] = []
        lows[ticker] = []
        closes[ticker] = []
        opens[ticker] = []
        try:
            for h, l, c, o in zip(high_all[ticker], low_all[ticker], close_all[ticker], open_all[ticker]):
                if (
                        h != 0.0
                        and not math.isnan(h)
                        and l != 0.0
                        and not math.isnan(l)
                        and c != 0.0
                        and not math.isnan(c)
                        and o != 0.0
                        and not math.isnan(o)
                ):
                    highs[ticker].append(h)
                    lows[ticker].append(l)
                    closes[ticker].append(c)
                    opens[ticker].append(o)
        except:
            pass
    return highs, lows, closes, opens


def get_closes(tickers, period='10y', interval='1d'):
    data = yf.download(tickers, period=period, interval=interval, auto_adjust=True)
    closes = {}
    close_all = data["Close"]
    for ticker in tickers:
        closes[ticker] = []
        try:
            for close in close_all[ticker]:
                if close != 0.0 and not math.isnan(close):
                    closes[ticker].append(close)
        except:
            pass
    return closes


def get_close_as_series(ticker, period='10y', interval='1d'):
    data = yf.Ticker(ticker).history(period=period, interval=interval)
    data = data.reset_index()
    data['Date'] = pd.to_datetime(data['Date'].dt.date)
    data = data.rename(columns={'Date': 'ds', 'Close': 'y'})
    data['unique_id'] = ticker
    data = data[['unique_id', 'ds', 'y']]
    return data


def get_name(ticker):
    info = yf.Ticker(ticker).info
    name = info["shortName"] or info["longName"]
    currency = info["currency"]
    return f'{name} ({ticker}) - {currency}'


def get_pe_ratio(ticker):
    try:
        pe_ratio = yf.Ticker(ticker).info.get("trailingPE")
        if pe_ratio is None or pe_ratio <= 0.0 or math.isnan(pe_ratio):
            return None
        return pe_ratio
    except:
        return None


def get_peg_ratio(ticker):
    try:
        peg_ratio = yf.Ticker(ticker).info.get("trailingPegRatio")
        if peg_ratio is None or peg_ratio <= 0.0 or math.isnan(peg_ratio):
            return None
        return peg_ratio
    except:
        return None


def get_ev_to_ebitda(ticker):
    try:
        ev_to_ebitda = yf.Ticker(ticker).info.get("enterpriseToEbitda")
        if ev_to_ebitda is None or ev_to_ebitda <= 0.0 or math.isnan(ev_to_ebitda):
            return None
        return ev_to_ebitda
    except:
        return None


def get_fair_value(ticker, growth_10y=None, growth_1y=None, backtest=False):
    try:
        if backtest:
            earnings_history = yf.Ticker(ticker).earnings_history
            current_year = earnings_history['epsActual'].iloc[0]
            next_year = earnings_history['epsActual'].iloc[-1]
        else:
            eps_trend = yf.Ticker(ticker).eps_trend
            current_year = eps_trend['current']['0y']
            next_year = eps_trend['current']['+1y']

        growth_value_estimate = 40.0
        if current_year > 0.0:
            growth_value_estimate = (next_year / current_year - 1.0) * 100.0
        if growth_value_estimate is None or growth_value_estimate <= 0.0 or math.isnan(growth_value_estimate):
            growth_value_estimate = 40.0
    except:
        growth_value_estimate = 40.0

    try:
        if growth_10y is not None:
            growth_value = ((growth_10y[-1] / growth_10y[0]) ** (1.0 / 10.0) - 1.0) * 100.0
        else:
            growth_value = ((growth_1y[-1] / growth_1y[0]) - 1.0) * 100.0
        growth_value = min(growth_value, growth_value_estimate)
        eps = yf.Ticker(ticker).info.get("trailingEps")
        if eps is None or eps <= 0.0 or math.isnan(eps) or growth_value <= 0.0:
            return None
        return eps * growth_value
    except:
        return None


def get_high_low_in_currency(ticker, to_convert=None, target_currency='EUR'):
    high, low = get_high_low(ticker)
    currency = get_currency(ticker)

    if currency == target_currency:
        return high, low

    conversion_ticker = f'{currency}{target_currency}=X' if currency != 'USD' else f'{target_currency}=X'
    conversion_rate = get_price(conversion_ticker)

    if to_convert is None:
        return high * conversion_rate, low * conversion_rate
    else:
        return high * conversion_rate, low * conversion_rate, to_convert * conversion_rate


def get_price_in_currency(ticker, to_convert=None, target_currency='EUR'):
    price = get_price(ticker)
    currency = get_currency(ticker)

    if currency == target_currency:
        return price

    conversion_ticker = f'{currency}{target_currency}=X' if currency != 'USD' else f'{target_currency}=X'
    conversion_rate = get_price(conversion_ticker)

    if to_convert is None:
        return price * conversion_rate
    else:
        return price * conversion_rate, to_convert * conversion_rate


def get_currency(ticker):
    info = yf.Ticker(ticker).info
    return info["currency"]


def extract_ticker_df(df, ticker):
    return df[ticker].copy().dropna(subset=[P.H.value, P.L.value, P.C.value, P.O.value]).loc(
        lambda x: (x[P.H.value] != 0) & (x[P.L.value] != 0) & (x[P.C.value] != 0) & (x[P.O.value] != 0)
    )


if __name__ == '__main__':
    # print(get_close_as_series('AAPL'))
    # print(get_price('AAPL'))
    # print(convert([1.0, 2.0]))
    # print(get_price_in_currency('AAPL'))
    print(yf.Ticker('AAPL').financials)
    print(yf.Ticker('AAPL').cash_flow)
    print(yf.Ticker('AAPL').balance_sheet)
    print(yf.Ticker('AAPL').capital_gains)
    print(yf.Ticker('AAPL').info)
    print(yf.Ticker('AAPL').income_stmt)
    print(yf.Ticker('AAPL').revenue_estimate)