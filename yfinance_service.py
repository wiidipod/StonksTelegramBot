import yfinance as yf
import math


def get_closes(tickers, period='10y', interval='1d'):
    data = yf.download(tickers, period=period, interval=interval, auto_adjust=True)
    closes = {}
    close_all = data["Close"]
    for ticker in tickers:
        closes[ticker] = []
        try:
            for i, close in enumerate(close_all[ticker]):
                if close != 0 and not math.isnan(close):
                    closes[ticker].append(close)
        except:
            pass
    return closes


def get_name(ticker):
    info = yf.Ticker(ticker).info
    name = info["shortName"] or info["longName"]
    return f'{name} ({ticker})'
