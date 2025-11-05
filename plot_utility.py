import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.gridspec as gridspec
import mplfinance as mpf
import yfinance as yf

import regression_utility
from yfinance_service import P
import yfinance_service
from message_utility import round_down, round_up
from constants import output_directory


def plot_with_constants_by_df(
        ticker,
        name,
        df,
        constants,
        yscale='linear',
):
    length = len(df)
    fourths = [[constant] * length for constant in constants]

    fig = plt.figure(figsize=(9.0, 9.0), dpi=300)
    fig.suptitle(name)

    fname = f'{output_directory}{ticker}_plot_with_constants.png'
    fig = plt.figure(figsize=(9.0, 9.0), dpi=300)
    fig.suptitle(name)
    subplot = fig.add_subplot(111)
    subplot.set_yscale(yscale)
    currency = yfinance_service.get_currency(ticker)
    subplot.set_ylabel(currency)
    subplot.set_xlabel('Date')
    subplot.grid(True)
    # for label in labels:
    #     subplot.fill_between(df.index, df[f'{label} (High)'], df[f'{label} (Low)'], label=label)
    for fourth in reversed(fourths):
        subplot.plot(df.index, fourth, label=f"{fourth[0]:16.8f} {currency}")
    subplot.fill_between(df.index, df[P.H.value], df[P.L.value], label='Price')
    subplot.legend()
    fig.tight_layout()
    fig.savefig(fname)
    return fname


def plot_with_constants(
        ticker,
        name,
        close,
        high,
        low,
        constants,
        yscale='linear',
        rsi=None,
        rsi_sma=None,
        macd=None,
        macd_signal=None,
        macd_diff=None
):
    length = len(close)
    fourths = [[constant] * length for constant in constants]

    fig = plt.figure(figsize=(9.0, 9.0), dpi=300)
    fig.suptitle(name)

    gs = gridspec.GridSpec(3, 1, height_ratios=[3, 1, 1])

    price_subplot = fig.add_subplot(gs[0])
    plot_with_colors(close, high, low, price_subplot, fourths, fourths, yscale)

    macd_subplot = fig.add_subplot(gs[1])
    plot_macd(
        macd[-length:],
        macd_diff[-length-1:],
        macd_signal[-length:],
        macd_subplot,
    )

    rsi_subplot = fig.add_subplot(gs[2])
    plot_rsi(
        rsi[-length:],
        rsi_sma[-length:],
        rsi_subplot,
    )

    fig.tight_layout()
    image_path = f'{output_directory}{ticker}_prediction_plot.png'
    fig.savefig(image_path)
    return image_path
    # fig.show()


def plot_prediction(
        ticker,
        name,
        series,
        predictions,
):
    last_data_point = series.iloc[-1]

    fig = plt.figure(figsize=(9.0, 9.0), dpi=100)
    fig.suptitle(name)

    price_subplot = fig.add_subplot(111)
    price_subplot.set_ylabel('Price')
    price_subplot.grid(True)
    price_subplot.set_yscale('linear')
    price_subplot.plot(series['ds'], series['y'], label='Actual')
    for column in predictions.columns:
        if column != 'ds' and column != 'unique_id':
            concatenated_ds = pd.concat([pd.Series([last_data_point['ds']]), predictions['ds']]).reset_index(drop=True)
            concatenated_column = pd.concat([pd.Series([last_data_point['y']]), predictions[column]]).reset_index(drop=True)
            price_subplot.plot(concatenated_ds, concatenated_column, label=column)

    price_subplot.legend()

    fig.tight_layout()
    image_path = f'{output_directory}{ticker}_prediction_plot.png'
    fig.savefig(image_path)
    fig.show()

    # return image_path


def plot_with_growths(
        ticker,
        name,
        close,
        high,
        low,
        growths_high,
        growths_low,
        yscale='log',
        show=False,
):
    fig = plt.figure(figsize=(9.0, 9.0), dpi=300)
    fig.suptitle(f'{name}: 10 years')

    price_subplot = fig.add_subplot(111)

    plot_with_colors(close, high, low, price_subplot, growths_high, growths_low, yscale)

    plt.tight_layout()
    image_path = f'{output_directory}{ticker}_plot.png'
    plt.savefig(image_path)

    if show:
        plt.show()

    return image_path


def plot_with_colors(close, high, low, plot, five_colors_high, five_colors_low, yscale):
    plot.set_yscale(yscale)
    plot.set_ylabel('Price')
    plot.fill_between(np.arange(len(close)), high, low)
    plot.grid(True)
    for i, (growth_high, growth_low) in enumerate(zip(five_colors_high, five_colors_low)):
        if i == 0:
            color = 'tab:red'
        elif i == 1:
            color = 'tab:purple'
        elif i == 2:
            color = 'tab:blue'
        elif i == 3:
            color = 'tab:cyan'
        elif i == 4:
            color = 'tab:green'
        else:
            color = 'tab:gray'
        plt.fill_between(np.arange(len(growth_high)), growth_high, growth_low, color=color, linestyle='dashed')
    # plt.plot(five_colors[2], color='tab:blue', linestyle='dashed')


def plot_bands(
        ticker,
        title,
        high,
        low,
        graphs,
        labels,
        yscale='linear',
):
    fig = plt.figure(figsize=(9.0, 9.0), dpi=300)
    fig.suptitle(f'{title}')
    price_subplot = fig.add_subplot(111)

    price_subplot.set_yscale(yscale)
    price_subplot.set_ylabel('Price')
    x = np.arange(len(high))
    for i, label in enumerate(reversed(labels)):
        price_subplot.fill_between(x, graphs[-2*i-1], graphs[-2*i-2], label=label)
    price_subplot.fill_between(x, high, low)

    price_subplot.grid(True)
    price_subplot.legend()

    fig.tight_layout()
    image_path = f'{output_directory}{ticker}_plot_bands.png'
    fig.savefig(image_path)

    return image_path


def plot_with_ta(
        ticker,
        name,
        close,
        high,
        low,
        smas=None,
        window_long=None,
        window_short=None,
        growths_high=None,
        growths_low=None,
        yscale='linear',
        start_index=0,
        end_index=250,
        rsi=None,
        rsi_sma=None,
        macd=None,
        macd_signal=None,
        macd_diff=None,
        # upperband=None,
        # lowerband=None,
):
    if smas is None:
        smas = []

    if growths_high is None or growths_low is None:
        growths_high = []
        growths_low = []

    x = np.arange(end_index - start_index)

    fig = plt.figure(figsize=(9.0, 9.0), dpi=300)
    fig.suptitle(f'{name}: 1 year')
    gs = gridspec.GridSpec(3, 1, height_ratios=[3, 1, 1])

    # Price
    price_subplot = fig.add_subplot(gs[0])

    price_subplot.set_yscale(yscale)
    price_subplot.set_ylabel('Price')

    price_subplot.grid(True)
    for i, (growth_high, growth_low) in enumerate(zip(growths_high[1:-1], growths_low[1:-1])):
        if i == 0:
            color = 'tab:purple'
        elif i == 1:
            color = 'tab:blue'
        elif i == 2:
            color = 'tab:cyan'
        else:
            color = 'tab:gray'
        # plt.plot(growth[start_index:end_index], color=color, linestyle='dashed')
        plt.fill_between(x, growth_high[start_index:end_index], growth_low[start_index:end_index], color=color, linestyle='dashed')

    # if upperband and lowerband:
    #     plot_supertrend(
    #         upperband[start_index:],
    #         lowerband[start_index:],
    #         price_subplot,
    #     )

    # price_subplot.plot(close[start_index:end_index], label='Close')
    price_subplot.fill_between(x, high[start_index:end_index], low[start_index:end_index])

    for i, sma in enumerate(smas):
        if i == 0:
            label = 'SMA-200'
        elif i == 1:
            label = f'EMA-{window_long}'
        else:
            label = f'EMA-{window_short}'
        price_subplot.plot(sma[start_index:end_index], label=label)

    price_subplot.legend()

    # MACD
    macd_subplot = fig.add_subplot(gs[1])
    plot_macd(
        macd[start_index:],
        macd_diff[start_index-1:],
        macd_signal[start_index:],
        macd_subplot,
    )

    # RSI
    rsi_subplot = fig.add_subplot(gs[2])
    plot_rsi(
        rsi[start_index:],
        rsi_sma[start_index:],
        rsi_subplot,
    )

    fig.tight_layout()
    image_path = f'{output_directory}{ticker}_plot_with_ta.png'
    fig.savefig(image_path)

    return image_path


# def plot_supertrend(upperband, lowerband, subplot):
#     subplot.plot(upperband, color='tab:red', label='Upperband')
#     subplot.plot(lowerband, color='tab:green', label='Lowerband')


def plot_rsi(rsi, rsi_sma, rsi_subplot):
    length = len(rsi)
    rsi_subplot.set_ylabel('RSI')
    rsi_subplot.plot(rsi, label='RSI')
    rsi_subplot.plot(rsi_sma, label='SMA')
    gray = 'tab:gray'
    rsi_subplot.plot([70] * length, color='tab:red', linestyle='dashed', label='Overbought')
    rsi_subplot.plot([50] * length, color=gray, linestyle='dashed')
    rsi_subplot.plot([30] * length, color='tab:green', linestyle='dashed', label='Oversold')
    rect = Rectangle((0, 30), length, 40, color=gray, alpha=0.3)
    rsi_subplot.add_patch(rect)
    rsi_subplot.grid(True)
    rsi_subplot.legend(loc='upper left')


def plot_macd(macd, macd_diff, macd_signal, macd_subplot):
    macd_subplot.set_ylabel('MACD')
    macd_subplot.plot(macd, label='MACD')
    macd_subplot.plot(macd_signal, label='Signal')
    colors = get_colors(macd_diff)
    macd_subplot.bar(np.arange(len(macd)), macd_diff[1:], color=colors)
    macd_subplot.grid(True)
    macd_subplot.legend(loc='upper left')


def get_colors(macd_diff):
    green = (0.0, 0.5, 0.0)
    red = (1.0, 0.0, 0.0)
    green2 = (0.0, 0.5, 0.0, 0.5)
    red2 = (1.0, 0.0, 0.0, 0.5)
    colors = []
    for macd0, macd1 in zip(macd_diff[:-1], macd_diff[1:]):
        if macd0 <= macd1 >= 0:
            colors.append(green)
        if 0 <= macd1 < macd0:
            colors.append(green2)
        if macd0 >= macd1 < 0:
            colors.append(red)
        if 0 > macd1 > macd0:
            colors.append(red2)
    return colors


def plot_reversal(df, ticker):
    fname = f'{output_directory}{ticker}_reversal_plot.png'
    title = yfinance_service.get_name(ticker)
    mpf.plot(
        df.iloc[-5:],
        volume=False,
        style='yahoo',
        type='candle',
        savefig=dict(fname=fname, dpi=300, pad_inches=0.25),
        title=title,
        tight_layout=True,
        figsize=(9.0, 9.0),
    )
    return fname


def plot_bands_by_labels(df, ticker, title, labels, subtitle=None, fname=None, yscale='linear', today=-1, close_only=False, sma_label=None):
    if fname is None:
        fname = f'{output_directory}{ticker}_two_bands_plot.png'

    fig = plt.figure(figsize=(9.0, 9.0), dpi=300)
    fig.suptitle(title)
    subplot = fig.add_subplot(111)

    if subtitle:
        subplot.set_title(subtitle)

    subplot.set_yscale(yscale)
    subplot.set_ylabel(yfinance_service.get_currency(ticker))
    subplot.set_xlabel('Date')
    subplot.grid(True)

    for label in labels:
        if not close_only:
            subplot.fill_between(df.index, df[f'{label} (High)'], df[f'{label} (Low)'], label=f'{label} ({round_up(df[f"{label} (High)"].iat[today])} / {round_down(df[f"{label} (Low)"].iat[today])})')
        else:
            subplot.plot(df.index, df[label], label=f'{label} ({round_down(df[label].iat[today])})')

    if not close_only:
        subplot.fill_between(df.index, df[P.H.value], df[P.L.value], label=f'Price ({round_up(df[P.H.value].iat[today])} / {round_down(df[P.L.value].iat[today])})')
    else:
        subplot.plot(df.index, df[P.C.value], label=f'Price ({round_up(df[P.C.value].iat[today])})')

    if sma_label:
        subplot.plot(df.index, df[sma_label], label=f'{sma_label} ({round_down(df[sma_label].iat[today])})')

    subplot.legend()
    fig.tight_layout()
    fig.savefig(fname)
    return fname


if __name__ == '__main__':
    # main_ticker = '^990100-USD-STRD'
    main_ticker = 'NVDA'

    df = yf.download(
        [main_ticker],
        period='10y',
        interval='1d',
        group_by='ticker',
    )
    ticker_df = yfinance_service.extract_ticker_df(df=df, ticker=main_ticker)

    future = len(df) // 10

    window = len(df) // 2
    ticker_df = regression_utility.add_window_growths(ticker_df, window=window, future=future, add_full_length_growth=True, add_string='5y')

    plot_path = plot_bands_by_labels(
        df=ticker_df,
        ticker=main_ticker,
        title=main_ticker,
        subtitle=main_ticker,
        labels=[
            'Growth',
            'Growth Lower',
            'Growth Upper',
            '5yGrowth',
            '5yGrowth Lower',
            '5yGrowth Upper',
        ],
        yscale='log',
        today=-1-future,
    )

    print(plot_path)
    print(ticker_df['Growth (High)'].iat[-1])
    print(ticker_df['Growth (Low)'].iat[-1])

    # main_name = yfinance_service.get_name(main_ticker)
    # main_high, main_low, main_close = yfinance_service.get_high_low_close(main_ticker, period='max', interval='1d')
    # fit_high, lower_fit_high, upper_fit_high, double_lower_fit_high, double_upper_fit_high, final_growth_high = regression_utility.get_daily_growths(main_high)
    # fit_low, lower_fit_low, upper_fit_low, double_lower_fit_low, double_upper_fit_low, final_growth_low = regression_utility.get_daily_growths(main_low)
    # fit_high_2, _, _, _, _, growth_of_fit_high = regression_utility.get_daily_growths(fit_high)
    # fit_low_2, _, _, _, _, growth_of_fit_low = regression_utility.get_daily_growths(fit_low)
    # fit_high_3, _, _, _, _, _ = regression_utility.get_daily_growths(fit_high_2)
    # fit_low_3, _, _, _, _, _ = regression_utility.get_daily_growths(fit_low_2)
    #
    # plot_with_growths(
    #     main_ticker,
    #     main_name,
    #     main_close,
    #     main_high,
    #     main_low,
    #     [fit_high, fit_high_2, fit_high_3],
    #     [fit_low, fit_low_2, fit_low_3],
    #     show=False,
    # )
