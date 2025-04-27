import asyncio

import message_utility
import telegram_service
import yfinance_service
from yfinance_service import P
import ta_utility
import plot_utility
import yfinance as yf


graph_window = 250


def analyze_reversal():
    tickers = [
        '^GDAXI',
        '^NDX',
        '^GSPC',
        # '^DJI',
        # '^MDAXI',
        '^STOXX50E',
        # '^N225',
        # '^TECDAX',
        # '^FCHI',
        '^FTSE',
    ]

    df = yf.download(tickers, period='5d', interval='1d')
    plot_paths = []

    for ticker in tickers:
        ticker_df = df.xs(key=ticker, axis=1, level=1)

        reversal = ta_utility.get_reversal_by_dataframe(ticker_df)

        if reversal is True:
            plot_paths.append(plot_utility.plot_reversal(ticker_df, ticker))

    return plot_paths


def analyze_dji():
    dji = '^DJI'
    window = 65
    df = yf.download(
        [dji],
        period='2y',
        interval='1d',
        group_by='ticker',
    )
    dji_df = yfinance_service.extract_ticker_df(df, dji)
    dji_df = ta_utility.add_emas(dji_df, window=window)

    dji_name = yfinance_service.get_name(dji)

    if dji_df[P.L.value].iat[-1] > dji_df[f"EMA-{window} (High)"].iat[-1]:
        title = f'{dji_name}: Buy US5L'
    elif dji_df[P.H.value].iat[-1] < dji_df[f"EMA-{window} (Low)"].iat[-1]:
        title = f'{dji_name}: Sell US5L'
    else:
        title = f'{dji_name}: Neutral US5L'

    labels = [
        f'EMA-{window}',
    ]

    plot_path = plot_utility.plot_bands_by_labels(
        df=dji_df.iloc[-250:],
        ticker=dji,
        title=title,
        labels=labels,
        fname='dji.png'
    )

    return plot_path


def analyze_golden_cross():
    nasdaq100 = '^NDX'
    window_short = 14
    window_long = 250
    df = yf.download(
        [nasdaq100],
        period='2y',
        interval='1d',
        group_by='ticker',
    )
    nasdaq100_df = yfinance_service.extract_ticker_df(df, nasdaq100)
    nasdaq100_df = ta_utility.add_smas(nasdaq100_df, window=window_long)
    nasdaq100_df = ta_utility.add_smas(nasdaq100_df, window=window_short)
    nasdaq100_name = yfinance_service.get_name(nasdaq100)

    if nasdaq100_df[f"SMA-{window_short} (Low)"].iat[-1] > nasdaq100_df[f"SMA-{window_long} (High)"].iat[-1]:
        title = f'{nasdaq100_name}: Buy TQQQ'
    elif nasdaq100_df[f"SMA-{window_short} (High)"].iat[-1] < nasdaq100_df[f"SMA-{window_long} (Low)"].iat[-1]:
        title = f'{nasdaq100_name}: Sell TQQQ'
    else:
        title = f'{nasdaq100_name}: Neutral TQQQ'

    labels = [
        f'SMA-{window_long}',
        f'SMA-{window_short}',
    ]

    plot_path = plot_utility.plot_bands_by_labels(
        df=nasdaq100_df.iloc[-250:],
        ticker=nasdaq100,
        title=title,
        labels=labels,
        fname='tqqq.png'
    )

    return plot_path


def analyze_amumbo():
    sp500 = '^GSPC'
    sma_window = 200
    ema_window = 65
    df = yf.download(
        [sp500],
        period='2y',
        interval='1d',
        group_by='ticker',
    )
    sp500_df = yfinance_service.extract_ticker_df(df, sp500)
    sp500_df = ta_utility.add_smas(sp500_df, window=sma_window)
    sp500_name = yfinance_service.get_name(sp500)

    if sp500_df[P.L.value].iat[-1] > sp500_df[f"SMA-{sma_window} (High)"].iat[-1]:
        title = f'{sp500_name}: Buy Amumbo'
    elif sp500_df[P.H.value].iat[-1] < sp500_df[f"SMA-{sma_window} (Low)"].iat[-1]:
        title = f'{sp500_name}: Sell Amumbo'
    else:
        title = f'{sp500_name}: Neutral Amumbo'

    labels = [
        f'SMA-{sma_window}',
    ]

    plot_path = plot_utility.plot_bands_by_labels(
        df=sp500_df.iloc[-max(sma_window, ema_window):],
        ticker=sp500,
        title=title,
        labels=labels,
        fname='amumbo.png'
    )

    return plot_path


def analyze_all():
    sp500 = '^GSPC'
    df = yf.download(
        [sp500],
        period='2y',
        interval='1d',
        group_by='ticker',
    )
    sp500_df = yfinance_service.extract_ticker_df(df, sp500)
    sp500_df = ta_utility.add_smas(sp500_df, window=200)
    # sp500_df = ta_utility.add_smas(sp500_df, window=250)
    # sp500_df = ta_utility.add_smas(sp500_df, window=14)
    sp500_df = ta_utility.add_emas(sp500_df, window=65)

    sp500_name = yfinance_service.get_name(sp500)

    if sp500_df[P.L.value].iat[-1] > sp500_df["SMA-200 (High)"].iat[-1]:
        title = f'{sp500_name} (2x: Buy)'
    elif sp500_df[P.H.value].iat[-1] < sp500_df["SMA-200 (Low)"].iat[-1]:
        title = f'{sp500_name} (2x: Sell)'
    else:
        title = f'{sp500_name} (2x: Neutral)'

    # if sp500_df["SMA-14 (Low)"].iat[-1] > sp500_df["SMA-250 (High)"].iat[-1]:
    #     title += f' | 3x: Buy'
    # elif sp500_df["SMA-14 (High)"].iat[-1] < sp500_df["SMA-250 (Low)"].iat[-1]:
    #     title += f' | 3x: Sell'
    # else:
    #     title += f' | 3x: Neutral'

    # if sp500_df[P.L.value].iat[-1] > sp500_df["EMA-65 (High)"].iat[-1]:
    #     title += f' | 5x: Buy)'
    # elif sp500_df[P.H.value].iat[-1] < sp500_df["EMA-65 (Low)"].iat[-1]:
    #     title += f' | 5x: Sell)'
    # else:
    #     title += f' | 5x: Neutral)'

    labels = [
        f'SMA-200',
        # f'EMA-65',
        # f'SMA-250',
        # f'SMA-14',
    ]

    plot_path = plot_utility.plot_bands_by_labels(
        df=sp500_df.iloc[-250:],
        ticker=sp500,
        title=title,
        labels=labels,
        fname='sp500.png'
    )

    return plot_path


if __name__ == '__main__':
    plot_paths = [
        # analyze_amumbo(),
        # analyze_golden_cross(),
        # analyze_dji(),
        analyze_all(),
    ] + analyze_reversal()

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(plot_paths, [], application))
