import numpy as np
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.gridspec as gridspec


def plot(
        ticker,
        name,
        close,
        sma_220,
        growths,
        yscale='log',
        start_index=0,
        end_index=250,
        rsi=None,
        rsi_sma=None,
        macd=None,
        macd_signal=None,
        macd_diff=None
):
    length = end_index - start_index

    fig = plt.figure(figsize=(9.0, 14.0))
    fig.suptitle(name)
    gs = gridspec.GridSpec(3, 1, height_ratios=[3, 1, 1])

    # Price
    price_subplot = fig.add_subplot(gs[0])

    price_subplot.set_yscale(yscale)
    price_subplot.set_ylabel('Price')
    price_subplot.plot(close[start_index:end_index])
    price_subplot.plot(sma_220[start_index:end_index])
    price_subplot.grid(True)
    for growth in growths:
        plt.plot(growth[start_index:end_index], color='gray', linestyle='dashed')

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
    rsi_subplot.plot([70] * length, color='gray', linestyle='dashed')
    rsi_subplot.plot([50] * length, color='gray', linestyle='dashed')
    rsi_subplot.plot([30] * length, color='gray', linestyle='dashed')
    rect = Rectangle((0, 30), length, 40, color='gray', alpha=0.3)
    rsi_subplot.add_patch(rect)
    rsi_subplot.grid(True)

    plt.tight_layout()
    image_path = f'{ticker}_plot.png'
    plt.savefig(image_path)
    plt.show()
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
