import asyncio

import regression_utility
import telegram_service
import yfinance_service
import ta_utility
import plot_utility


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
        sma_short_high[-window_long:],
        sma_short_low[-window_long:],
        sma_long_high[-window_long:],
        sma_long_low[-window_long:],
    ]

    labels = [
        f'SMA-{window_short}',
        f'SMA-{window_long}',
    ]

    plot_path = plot_utility.plot_bands(
        'tqqq',
        title,
        nasdaq100_high[-window_long:],
        nasdaq100_low[-window_long:],
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
        sma_200_high[-window:],
        sma_200_low[-window:],
    ]

    labels = [
        f'SMA-{window}',
    ]

    plot_path = plot_utility.plot_bands(
        'amumbo',
        title,
        sp500_high[-window:],
        sp500_low[-window:],
        graphs,
        labels,
        yscale='linear'
    )

    return plot_path


if __name__ == '__main__':
    plot_paths = [
        analyze_amumbo(),
        analyze_golden_cross()
    ]

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(plot_paths, [], application))
    # asyncio.run(telegram_service.send_all(analyze_amumbo(), [], application))
