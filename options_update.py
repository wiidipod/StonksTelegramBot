import asyncio

import message_utility
import plot_utility
import regression_utility
import ta_utility
import telegram_service
import ticker_service
import yfinance_service
from tqdm import tqdm


def chunk_list(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


if __name__ == '__main__':
    tickers = ticker_service.get_all_tickers()
    future = 250

    upsides = {}
    all_plot_with_ta_paths = {}
    all_plot_paths = {}
    all_message_paths = {}

    ticker_chunks = chunk_list(tickers, 100)

    for i, ticker_chunk in enumerate(ticker_chunks):
        print(f'Processing chunk {i + 1} of {len(tickers) // 100 + 1}...')
        closes = yfinance_service.get_closes(ticker_chunk, period='10y', interval='1d')

        for ticker in tqdm(ticker_chunk):
            close = closes[ticker]

            if len(close) < 2500:
                continue

            rsi, rsi_sma = ta_utility.calculate_rsi(close)
            if rsi[-1] > 70.0 or rsi_sma[-1] > 70.0:
                continue

            macd, macd_signal, macd_diff = ta_utility.calculate_macd(close)
            if macd_diff[-1] < 0.0:
                continue

            growth, lower_growth, upper_growth, lower_border, upper_border = regression_utility.get_growths(close, future=future)
            if growth[-future] >= growth[-1] or lower_growth[-future] <= close[-1]:
                continue

            upside = lower_growth[-1] / close[-1] - 1.0
            downside = 1.0 - lower_border[-1] / close[-1]
            if upside < 0.0 or downside > 0.0:
                continue

            pe_ratio = yfinance_service.get_pe_ratio(ticker)
            if pe_ratio is None:
                continue

            upside = upside / pe_ratio * 20.0
            upsides[ticker] = upside

            name = f'{yfinance_service.get_name(ticker)} - Upside: {upside:.2%}'
            growths = [lower_border, lower_growth, growth, upper_growth, upper_border]

            plot_with_ta_path = plot_utility.plot_with_ta(
                ticker,
                name,
                close,
                ta_utility.calculate_sma_220(close),
                growths,
                start_index=len(close) - future,
                end_index=len(close),
                rsi=rsi,
                rsi_sma=rsi_sma,
                macd=macd,
                macd_signal=macd_signal,
                macd_diff=macd_diff,
            )

            plot_path = plot_utility.plot(
                ticker,
                name,
                close,
                growths,
            )

            message_path = message_utility.write_message(
                ticker,
                name,
                close,
                ta_utility.calculate_sma_220(close),
                growths,
                future=future,
                rsi=rsi,
                rsi_sma=rsi_sma,
                macd=macd,
                macd_signal=macd_signal,
                macd_diff=macd_diff,
            )

            all_plot_with_ta_paths[ticker] = plot_with_ta_path
            all_plot_paths[ticker] = plot_path
            all_message_paths[ticker] = message_path

    plot_paths = []
    message_paths = []

    sorted_upsides = sorted(upsides.items(), key=lambda x: x[1], reverse=True)
    for ticker, upside in sorted_upsides[:10]:
        print(f"{ticker} - Upside: {upside:.2%}")
        plot_paths.append(all_plot_with_ta_paths[ticker])
        plot_paths.append(all_plot_paths[ticker])
        message_paths.append(all_message_paths[ticker])

        # name = yfinance_service.get_name(ticker)
        # close = yfinance_service.get_closes([ticker])[ticker]
        # fit, lower_fit, upper_fit, lower_border, upper_border = regression_utility.get_growths(close, future=0)
        # growths = [lower_border, lower_fit, fit, upper_fit, upper_border]
        # plot_with_ta_path = plot_utility.plot(ticker, name, close, growths)
        # plot_paths.append(plot_with_ta_path)

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(plot_paths, message_paths, application))
