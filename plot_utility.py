import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.gridspec as gridspec

import regression_utility
import yfinance_service


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

    plt.tight_layout()
    image_path = f'{ticker}_prediction_plot.png'
    plt.savefig(image_path)
    plt.show()

    # return image_path


def plot(
        ticker,
        name,
        close,
        growths,
        yscale='log',
):
    fig = plt.figure(figsize=(9.0, 9.0), dpi=300)
    fig.suptitle(name)

    price_subplot = fig.add_subplot(111)
    price_subplot.set_yscale(yscale)
    price_subplot.set_ylabel('Price')
    price_subplot.plot(close)
    price_subplot.grid(True)
    for i, growth in enumerate(growths):
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
        plt.plot(growth, color=color, linestyle='dashed')

    plt.tight_layout()
    image_path = f'{ticker}_plot.png'
    plt.savefig(image_path)

    return image_path


def plot_with_ta(
        ticker,
        name,
        close,
        sma_220,
        growths,
        yscale='linear',
        start_index=0,
        end_index=250,
        rsi=None,
        rsi_sma=None,
        macd=None,
        macd_signal=None,
        macd_diff=None
):
    length = end_index - start_index

    fig = plt.figure(figsize=(9.0, 9.0), dpi=300)
    fig.suptitle(name)
    gs = gridspec.GridSpec(3, 1, height_ratios=[3, 1, 1])

    # Price
    price_subplot = fig.add_subplot(gs[0])

    price_subplot.set_yscale(yscale)
    price_subplot.set_ylabel('Price')
    price_subplot.plot(close[start_index:end_index])
    price_subplot.plot(sma_220[start_index:end_index])
    price_subplot.grid(True)
    for i, growth in enumerate(growths[1:-1]):
        if i == 0:
            color = 'tab:purple'
        elif i == 1:
            color = 'tab:blue'
        elif i == 2:
            color = 'tab:cyan'
        else:
            color = 'tab:gray'
        plt.plot(growth[start_index:end_index], color=color, linestyle='dashed')

    # MACD
    macd_subplot = fig.add_subplot(gs[1])
    macd_subplot.set_ylabel('MACD')
    macd_subplot.plot(macd[start_index:])
    macd_subplot.plot(macd_signal[start_index:])
    colors = get_colors(macd_diff, start_index)
    macd_subplot.bar(np.arange(length), macd_diff[start_index:], color=colors)
    macd_subplot.grid(True)

    # RSI
    rsi_subplot = fig.add_subplot(gs[2])
    rsi_subplot.set_ylabel('RSI')
    rsi_subplot.plot(rsi[start_index:])
    rsi_subplot.plot(rsi_sma[start_index:])
    color = 'tab:gray'
    rsi_subplot.plot([70] * length, color=color, linestyle='dashed')
    rsi_subplot.plot([50] * length, color=color, linestyle='dashed')
    rsi_subplot.plot([30] * length, color=color, linestyle='dashed')
    rect = Rectangle((0, 30), length, 40, color=color, alpha=0.3)
    rsi_subplot.add_patch(rect)
    rsi_subplot.grid(True)

    plt.tight_layout()
    image_path = f'{ticker}_plot_with_ta.png'
    plt.savefig(image_path)

    return image_path


def get_colors(macd_diff, start_index):
    green = (0.0, 0.5, 0.0)
    red = (1.0, 0.0, 0.0)
    green2 = (0.0, 0.5, 0.0, 0.5)
    red2 = (1.0, 0.0, 0.0, 0.5)
    colors = []
    for macd0, macd1 in zip(macd_diff[start_index-1:-1], macd_diff[start_index:]):
        if macd0 <= macd1 >= 0:
            colors.append(green)
        if 0 <= macd1 < macd0:
            colors.append(green2)
        if macd0 >= macd1 < 0:
            colors.append(red)
        if 0 > macd1 > macd0:
            colors.append(red2)
    return colors


if __name__ == '__main__':
    ticker = 'PUM.DE'
    name = yfinance_service.get_name(ticker)
    close = yfinance_service.get_closes([ticker])[ticker]
    fit, lower_fit, upper_fit, lower_border, upper_border = regression_utility.get_growths(close, future=250)

    plot(
        ticker,
        name,
        close,
        [lower_border, lower_fit, fit, upper_fit, upper_border],
    )
