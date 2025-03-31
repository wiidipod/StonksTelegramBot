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


def get_pe_ratio(ticker, limit=40.0):
    info = yf.Ticker(ticker).info
    forward_pe = info.get("forwardPE")
    trailing_pe = info.get("trailingPE")
    if (
        forward_pe is None
            or trailing_pe is None
            or forward_pe == 0
            or trailing_pe == 0
            or math.isnan(forward_pe)
            or math.isnan(trailing_pe)
            or forward_pe > limit
            or trailing_pe > limit
    ):
        return None
    return (max(forward_pe, 10.0) + max(trailing_pe, 10.0)) / 2.0


if __name__ == '__main__':
    print(get_pe_ratio('^NDX'))
