import asyncio

import regression_utility
import telegram_service
import yfinance_service
import ta_utility
import plot_utility


def analyze_golden_cross():
    nasdaq100 = '^NDX'
    window_long = 250
    window_short = 14
    high, lows, _, _ = yfinance_service.get_prices([nasdaq100], period='max', interval='1d')
    high = high[nasdaq100]
    low = lows[nasdaq100]
    high_sma_long = ta_utility.get_sma(high, window=window_long)
    low_sma_long = ta_utility.get_sma(low, window=window_long)
    high_sma_short = ta_utility.get_sma(high, window=window_short)
    low_sma_short = ta_utility.get_sma(low, window=window_short)
    name = yfinance_service.get_name(nasdaq100)

    if low_sma_short[-1] > high_sma_long[-1]:
        name += ': Buy'
    elif high_sma_short[-1] < low_sma_long[-1]:
        name += ': Sell'
    else:
        name += ': Neutral'

    graphs = [
        high_sma_long[-window_long:],
        low_sma_long[-window_long:],
        high_sma_short[-window_long:],
        low_sma_short[-window_long:]
    ]

    labels = [
        f'SMA-{window_long}',
        f'SMA-{window_short}',
    ]

    graphs, labels = get_growth_graphs_and_labels(graphs, high, labels, low, window_long)

    plot_path = plot_utility.plot_bands(
        '3xnasdaq100',
        name,
        high[-window_long:],
        low[-window_long:],
        graphs=graphs,
        labels=labels,
        yscale='log',
    )

    return plot_path


def get_growth_graphs_and_labels(graphs, high, labels, low, window):
    h_growth, h_lower_growth, h_upper_growth, h_double_lower_growth, h_double_upper_growth = regression_utility.get_growths(
        high)
    l_growth, l_lower_growth, l_upper_growth, l_double_lower_growth, l_double_upper_growth = regression_utility.get_growths(
        low)
    graphs += [
        h_growth[-window:],
        l_growth[-window:],
        h_lower_growth[-window:],
        l_lower_growth[-window:],
        h_upper_growth[-window:],
        l_upper_growth[-window:],
    ]
    labels += [
        'Growth',
        'Lower Growth',
        'Upper Growth',
    ]
    return graphs, labels


def analyze_amumbo():
    sp500 = '^GSPC'
    window = 200
    highs, lows, _, _ = yfinance_service.get_prices([sp500], period='max', interval='1d')
    high = highs[sp500]
    low = lows[sp500]
    high_sma_200 = ta_utility.get_sma(high, window=window)
    low_sma_200 = ta_utility.get_sma(low, window=window)
    name = yfinance_service.get_name(sp500)

    if low[-1] > high_sma_200[-1]:
        name += ': Buy'
    elif high[-1] < low_sma_200[-1]:
        name += ': Sell'
    else:
        name += ': Neutral'

    graphs = [
        high_sma_200[-window:],
        low_sma_200[-window:],
    ]

    labels = [
        f'SMA-{window}',
    ]

    graphs, labels = get_growth_graphs_and_labels(graphs, high, labels, low, window)

    plot_path = plot_utility.plot_bands(
        'amumbo',
        name,
        high[-window:],
        low[-window:],
        graphs,
        labels,
        yscale='log'
    )

    return plot_path


if __name__ == '__main__':
    plot_paths = [analyze_amumbo(), analyze_golden_cross()]

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(plot_paths, [], application))
