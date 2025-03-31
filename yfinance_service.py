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
    try:
        pe_ratio = yf.Ticker(ticker).info.get("trailingPE")
        if pe_ratio is None or pe_ratio == 0 or math.isnan(pe_ratio):
            return None
        return pe_ratio
    except:
        return None


def get_peg_ratio(ticker):
    try:
        peg_ratio = yf.Ticker(ticker).info.get("trailingPegRatio")
        if peg_ratio is None or peg_ratio == 0 or math.isnan(peg_ratio):
            return None
        return peg_ratio
    except:
        return None



if __name__ == '__main__':
    print(get_peg_ratio('AAPL'))
