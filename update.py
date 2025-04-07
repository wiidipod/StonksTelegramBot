import asyncio
from tqdm import tqdm
import regression_utility
import ta_utility
import telegram_service
import yfinance_service
import plot_utility
import message_utility


if __name__ == '__main__':
    defaults = [
        '^GSPC',
        'BTC-EUR',
        'GC=F',
    ]

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
        'BTC-EUR',
        'GME',
        'GC=F',
    ]
    future = 250

    closes = yfinance_service.get_closes(tickers, period='max', interval='1d')

    upsides = {}
    all_plot_with_ta_paths = {}
    all_plot_paths = {}
    all_message_paths = {}

    for ticker in tqdm(tickers):
        close = closes[ticker]
        is_default = ticker in defaults

        if len(close) < 2500 and not is_default:
            continue

        technicals = ta_utility.get_technicals(close)
        bullish, rsi, rsi_sma, macd, macd_signal, macd_diff = technicals
        if not bullish and not is_default:
            continue

        growth, lower_growth, upper_growth, double_lower_growth, double_upper_growth = regression_utility.get_growths(close, future=future)
        if growth[-future] >= growth[-1] and not is_default:
            continue

        if lower_growth[-1] < close[-1] and not is_default:
            continue

        one_year_estimate = growth[-1]
        upside = one_year_estimate / close[-1] - 1.0

        if one_year_estimate <= close[-1] and not is_default:
            continue

        upsides[ticker] = upside

        sma_200 = ta_utility.get_sma(close)
        sma_325 = ta_utility.get_sma(close, window=325)
        sma_50 = ta_utility.get_sma(close, window=50)
        name = yfinance_service.get_name(ticker)

        close = close[-2500:]
        double_lower_growth = double_lower_growth[-2500 - future:]
        lower_growth = lower_growth[-2500 - future:]
        growth = growth[-2500 - future:]
        upper_growth = upper_growth[-2500 - future:]
        double_upper_growth = double_upper_growth[-2500 - future:]
        macd = macd[-2500:]
        macd_signal = macd_signal[-2500:]
        macd_diff = macd_diff[-2500:]
        rsi = rsi[-2500:]
        rsi_sma = rsi_sma[-2500:]
        sma_200 = sma_200[-2500:]
        sma_325 = sma_325[-2500:]
        sma_50 = sma_50[-2500:]
        growths = [double_lower_growth, lower_growth, growth, upper_growth, double_upper_growth]
        smas = [sma_200, sma_325, sma_50]

        plot_with_ta_path = plot_utility.plot_with_ta(
            ticker,
            name,
            close,
            smas=smas,
            growths=growths,
            start_index=len(close) - future,
            end_index=len(close),
            rsi=rsi,
            rsi_sma=rsi_sma,
            macd=macd,
            macd_signal=macd_signal,
            macd_diff=macd_diff,
        )

        plot_path = plot_utility.plot_with_growths(
            ticker,
            name,
            close,
            growths,
        )

        message_path = message_utility.write_message(
            ticker,
            name,
            close,
            smas=smas,
            growths=growths,
            future=future,
            rsi=rsi,
            rsi_sma=rsi_sma,
            macd=macd,
            macd_signal=macd_signal,
            macd_diff=macd_diff,
            one_year_estimate=one_year_estimate,
            upside=upside,
        )

        all_plot_with_ta_paths[ticker] = plot_with_ta_path
        all_plot_paths[ticker] = plot_path
        all_message_paths[ticker] = message_path

    plot_paths = []
    message_paths = []

    sorted_upsides = sorted(upsides.items(), key=lambda x: x[1], reverse=True)
    for ticker, upside in sorted_upsides:
        print(f"{ticker}\n    Upside: {upside:.2%}")
        plot_paths.append(all_plot_with_ta_paths[ticker])
        plot_paths.append(all_plot_paths[ticker])
        message_paths.append(all_message_paths[ticker])

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(plot_paths, message_paths, application))
