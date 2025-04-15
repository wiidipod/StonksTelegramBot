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

    # highs, lows, closes, opens = yfinance_service.get_prices(tickers, period='5d', interval='1d')
    df = yf.download(tickers, period='5d', interval='1d')
    # message = 'Reversals\n\n'
    zero_reversals = True
    plot_paths = []

    for ticker in tickers:
        ticker_df = df.xs(key=ticker, axis=1, level=1)


        reversal = ta_utility.get_reversal_by_dataframe(ticker_df)

        if reversal is True:
            plot_paths.append(plot_utility.plot_reversal(ticker_df, ticker))
            zero_reversals = False
            # message += f'{ticker} ``` {ticker_df[P.H.value].iat[-1]:16.8f} \n {ticker_df[P.L.value].iat[-1]:16.8f} ``` \n'

    # if zero_reversals:
    #     message += 'None found'

    return plot_paths #message_utility.save_message(message, 'reversal')

def analyze_golden_cross():
    nasdaq100 = '^NDX'
    tqqq = 'QQQ3.MI'
    window_short = 14
    window_long = 250
    nasdaq100_high, nasdaq100_low, _ = yfinance_service.get_high_low_close(nasdaq100, period='2y', interval='1d')
    tqqq_high, tqqq_low, _ = yfinance_service.get_high_low_close(tqqq, period='2y', interval='1d')
    sma_short_high = ta_utility.get_sma(nasdaq100_high, window=window_short)
    sma_short_low = ta_utility.get_sma(nasdaq100_low, window=window_short)
    sma_long_high = ta_utility.get_sma(nasdaq100_high, window=window_long)
    sma_long_low = ta_utility.get_sma(nasdaq100_low, window=window_long)
    nasdaq100_name = yfinance_service.get_name(nasdaq100)
    stop_sell = 1.0 / 118.0 * (7.0 * sum(tqqq_low[-249:]) - 125.0 * sum(tqqq_high[-13:]))
    stop_buy = 1.0 / 118.0 * (7.0 * sum(tqqq_high[-249:]) - 125.0 * sum(tqqq_low[-13:]))

    if sma_short_low[-1] > sma_long_high[-1]:
        title = f'{nasdaq100_name}: Buy TQQQ (Stop Sell @ {stop_sell:.8f})'
    elif sma_short_high[-1] < sma_long_low[-1]:
        title = f'{nasdaq100_name}: Sell TQQQ (Stop Buy @ {stop_buy:.8f})'
    else:
        title = f'{nasdaq100_name}: Neutral TQQQ (Stop Sell @ {stop_sell:.8f} / Stop Buy @ {stop_buy:.8f})'

    graphs = [
        sma_short_high[-graph_window:],
        sma_short_low[-graph_window:],
        sma_long_high[-graph_window:],
        sma_long_low[-graph_window:],
    ]

    labels = [
        f'SMA-{window_short}',
        f'SMA-{window_long}',
    ]

    plot_path = plot_utility.plot_bands(
        'tqqq',
        title,
        nasdaq100_high[-graph_window:],
        nasdaq100_low[-graph_window:],
        graphs,
        labels,
        yscale='linear'
    )

    return plot_path


def analyze_amumbo():
    sp500 = '^GSPC'
    amumbo = 'CL2.PA'
    window = 200
    sp500_high, sp500_low, _ = yfinance_service.get_high_low_close(sp500, period='2y', interval='1d')
    amumbo_high, amumbo_low, _ = yfinance_service.get_high_low_close(amumbo, period='1y', interval='1d')
    sma_200_high = ta_utility.get_sma(sp500_high, window=window)
    sma_200_low = ta_utility.get_sma(sp500_low, window=window)
    sp500_name = yfinance_service.get_name(sp500)

    if sp500_low[-1] > sma_200_high[-1]:
        stop_sell = sum(amumbo_low[-window:]) / window
        title = f'{sp500_name}: Buy Amumbo (Stop Sell @ {stop_sell:.8f})'
    elif sp500_high[-1] < sma_200_low[-1]:
        stop_buy = sum(amumbo_high[-window:]) / window
        title = f'{sp500_name}: Sell Amumbo (Stop Buy @ {stop_buy:.8f})'
    else:
        title = f'{sp500_name}: Neutral Amumbo'

    graphs = [
        sma_200_high[-graph_window:],
        sma_200_low[-graph_window:],
    ]

    labels = [
        f'SMA-{window}',
    ]

    plot_path = plot_utility.plot_bands(
        'amumbo',
        title,
        sp500_high[-graph_window:],
        sp500_low[-graph_window:],
        graphs,
        labels,
        yscale='linear'
    )

    return plot_path


if __name__ == '__main__':
    plot_paths = [
        analyze_amumbo(),
        analyze_golden_cross()
    ] + analyze_reversal()

    # message_paths = [
    #     analyze_reversal(),
    # ]

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(plot_paths, [], application))
    # asyncio.run(telegram_service.send_all(analyze_amumbo(), [], application))
