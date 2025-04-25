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
        '^DJI',
        '^MDAXI',
        '^STOXX50E',
        '^N225',
        '^TECDAX',
        '^FCHI',
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

def analyze_golden_cross():
    nasdaq100 = '^NDX'
    tqqq = 'QQQ3.MI'
    window_short = 14
    window_long = 250
    # nasdaq100_high, nasdaq100_low, _ = yfinance_service.get_high_low_close(nasdaq100, period='2y', interval='1d')
    # tqqq_high, tqqq_low, _ = yfinance_service.get_high_low_close(tqqq, period='2y', interval='1d')
    df = yf.download(
        [nasdaq100, tqqq],
        period='2y',
        interval='1d',
        group_by='ticker',
    )
    # nasdaq100_df = df.xs(key=nasdaq100, axis=1, level=1).copy()
    # tqqq_df = df.xs(key=tqqq, axis=1, level=1).copy()
    nasdaq100_df = yfinance_service.extract_ticker_df(df, nasdaq100)
    tqqq_df = yfinance_service.extract_ticker_df(df, tqqq)
    nasdaq100_df = ta_utility.add_smas(nasdaq100_df, window=window_long)
    nasdaq100_df = ta_utility.add_smas(nasdaq100_df, window=window_short)

    # sma_short_high = ta_utility.get_sma(nasdaq100_high, window=window_short)
    # sma_short_low = ta_utility.get_sma(nasdaq100_low, window=window_short)
    # sma_long_high = ta_utility.get_sma(nasdaq100_high, window=window_long)
    # sma_long_low = ta_utility.get_sma(nasdaq100_low, window=window_long)
    nasdaq100_name = yfinance_service.get_name(nasdaq100)

    # stop_sell = 1.0 / 118.0 * (7.0 * sum(tqqq_df[P.L.value].iloc[-249:]) - 125.0 * sum(tqqq_df[P.H.value].iloc[-13:]))
    # stop_buy = 1.0 / 118.0 * (7.0 * sum(tqqq_df[P.H.value].iloc[-249:]) - 125.0 * sum(tqqq_df[P.L.value].iloc[-13:]))

    # stop_sell = 1.0 / 118.0 * (7.0 * sum(tqqq_low[-249:]) - 125.0 * sum(tqqq_high[-13:]))
    # stop_buy = 1.0 / 118.0 * (7.0 * sum(tqqq_high[-249:]) - 125.0 * sum(tqqq_low[-13:]))

    # if sma_short_low[-1] > sma_long_high[-1]:
    if nasdaq100_df[f"SMA-{window_short} (Low)"].iat[-1] > nasdaq100_df[f"SMA-{window_long} (High)"].iat[-1]:
        title = f'{nasdaq100_name}: Buy TQQQ'  # (Stop Sell @ {stop_sell:.8f})'
    # elif sma_short_high[-1] < sma_long_low[-1]:
    elif nasdaq100_df[f"SMA-{window_short} (High)"].iat[-1] < nasdaq100_df[f"SMA-{window_long} (Low)"].iat[-1]:
        title = f'{nasdaq100_name}: Sell TQQQ'  # (Stop Buy @ {stop_buy:.8f})'
    else:
        title = f'{nasdaq100_name}: Neutral TQQQ'  # (Stop Sell @ {stop_sell:.8f} / Stop Buy @ {stop_buy:.8f})'

    labels = [
        f'SMA-{window_long}',
        f'SMA-{window_short}',
    ]

    # plot_path = plot_utility.plot_bands(
    #     'tqqq',
    #     title,
    #     nasdaq100_high[-graph_window:],
    #     nasdaq100_low[-graph_window:],
    #     graphs,
    #     labels,
    #     yscale='linear'
    # )

    plot_path = plot_utility.plot_bands_by_labels(
        df=nasdaq100_df.iloc[-window_long:],
        ticker=nasdaq100,
        title=title,
        labels=labels,
        fname='tqqq.png'
    )

    return plot_path


def analyze_amumbo():
    sp500 = '^GSPC'
    amumbo = 'CL2.PA'
    sma_window = 200
    ema_window = 65
    df = yf.download(
        [sp500, amumbo],
        period='2y',
        interval='1d',
        group_by='ticker',
    )
    # sp500_df = df.xs(key=sp500, axis=1, level=1).copy()
    # amumbo_df = df.xs(key=amumbo, axis=1, level=1).copy()
    sp500_df = yfinance_service.extract_ticker_df(df, sp500)
    amumbo_df = yfinance_service.extract_ticker_df(df, amumbo)
    sp500_df = ta_utility.add_smas(sp500_df, window=sma_window)
    sp500_df = ta_utility.add_emas(sp500_df, window=ema_window)
    amumbo_df = ta_utility.add_smas(amumbo_df, window=sma_window)
    sp500_name = yfinance_service.get_name(sp500)

    # stop_sell = amumbo_df[f"SMA-{sma_window} (Low)"].iat[-1]
    # stop_buy = amumbo_df[f"SMA-{sma_window} (High)"].iat[-1]

    if sp500_df[P.L.value].iat[-1] > sp500_df[f"SMA-{sma_window} (High)"].iat[-1]:
        title = f'{sp500_name}: Buy Amumbo'  # (Stop Sell @ {stop_sell:.8f})'
    elif sp500_df[P.H.value].iat[-1] < sp500_df[f"SMA-{sma_window} (Low)"].iat[-1]:
        title = f'{sp500_name}: Sell Amumbo'  # (Stop Buy @ {stop_buy:.8f})'
    else:
        title = f'{sp500_name}: Neutral Amumbo'  # (Stop Sell @ {stop_sell:.8f} / Stop Buy @ {stop_buy:.8f})'

    if sp500_df[P.L.value].iat[-1] > sp500_df[f"EMA-{ema_window} (High)"].iat[-1]:
        title += ' / Buy US5L'
    elif sp500_df[P.H.value].iat[-1] < sp500_df[f"EMA-{ema_window} (Low)"].iat[-1]:
        title += ' / Sell US5L'
    else:
        title += ' / Neutral US5L'

    labels = [
        f'SMA-{sma_window}',
        f'EMA-{ema_window}',
    ]

    plot_path = plot_utility.plot_bands_by_labels(
        df=sp500_df.iloc[-max(sma_window, ema_window):],
        ticker=sp500,
        title=title,
        labels=labels,
        fname='amumbo.png'
    )

    return plot_path


if __name__ == '__main__':
    plot_paths = [
        analyze_amumbo(),
        analyze_golden_cross()
    ] + analyze_reversal()

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(plot_paths, [], application))
