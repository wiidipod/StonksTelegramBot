import pandas as pd
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
    return f'{name} ({ticker})'


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


def get_fair_value(ticker, growth, backtest=False):
    try:
        if backtest:
            earnings_history = yf.Ticker(ticker).earnings_history
            current_year = earnings_history['epsActual'].iloc[0]
            next_year = earnings_history['epsActual'].iloc[-1]
        else:
            eps_trend = yf.Ticker(ticker).eps_trend
            current_year = eps_trend['current']['0y']
            next_year = eps_trend['current']['+1y']

        growth_value_estimate = (next_year / current_year - 1.0) * 100.0
        if growth_value_estimate is None or growth_value_estimate <= 0.0 or math.isnan(growth_value_estimate):
            growth_value_estimate = 40.0
    except:
        growth_value_estimate = 40.0

    try:
        growth_value = ((growth[-1] / growth[0]) ** (1.0 / 10.0) - 1.0) * 100.0
        growth_value = min(growth_value, growth_value_estimate)
        eps = yf.Ticker(ticker).info.get("trailingEps")
        if eps is None or eps <= 0.0 or math.isnan(eps) or growth_value <= 0.0:
            return None
        return eps * growth_value
    except:
        return None


if __name__ == '__main__':
    print(get_close_as_series('AAPL'))
