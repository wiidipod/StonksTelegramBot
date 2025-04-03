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
    backtest = False

    fair_values = {}
    upsides = {}
    peg_ratios = {}
    one_year_estimates = {}
    all_plot_with_ta_paths = {}
    all_plot_paths = {}
    all_message_paths = {}

    ticker_chunks = chunk_list(tickers, 100)

    for i, ticker_chunk in enumerate(ticker_chunks):
        print(f'Processing chunk {i + 1} of {len(tickers) // 100 + 1}...')

        if backtest:
            period = 'max'
            start_index = -2500 - future
            end_index = -future
        else:
            period = '10y'
            start_index = 0
            end_index = -1

        closes = yfinance_service.get_closes(ticker_chunk, period=period, interval='1d')

        for ticker in tqdm(ticker_chunk):
            close = closes[ticker][start_index:end_index]

            if len(close) < 2500:
                continue

            rsi, rsi_sma, macd, macd_signal, macd_diff = ta_utility.get_technicals(close)
            if rsi is None and not backtest:
                continue

            peg_ratio = yfinance_service.get_peg_ratio(ticker)
            if peg_ratio is None or peg_ratio > 1.0 and not backtest:
                continue

            growth, lower_growth, upper_growth, lower_border, upper_border = regression_utility.get_growths(close, future=future)
            if growth[-future] >= growth[-1]:
                continue

            fair_value = yfinance_service.get_fair_value(ticker, growth[:-future], backtest=backtest)
            if fair_value is None or fair_value <= 0.0:
                continue

            one_year_estimate = min(lower_growth[-1], fair_value)
            if one_year_estimate <= close[-1]:
                continue

            upside = one_year_estimate / close[-1] - 1.0
            if upside <= 0.0:
                continue

            fair_values[ticker] = fair_value
            upsides[ticker] = upside
            peg_ratios[ticker] = peg_ratio
            one_year_estimates[ticker] = one_year_estimate

            name = f'{yfinance_service.get_name(ticker)}'
            growths = [lower_border, lower_growth, growth, upper_growth, upper_border]

            plot_with_ta_path = plot_utility.plot_with_ta(
                ticker,
                name,
                close,
                ta_utility.get_sma(close),
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
                ta_utility.get_sma(close),
                growths,
                future=future,
                rsi=rsi,
                rsi_sma=rsi_sma,
                macd=macd,
                macd_signal=macd_signal,
                macd_diff=macd_diff,
                peg_ratio=peg_ratio,
                fair_value=fair_value,
                one_year_estimate=one_year_estimate,
                upside=upside,
            )

            all_plot_with_ta_paths[ticker] = plot_with_ta_path
            all_plot_paths[ticker] = plot_path
            all_message_paths[ticker] = message_path

    plot_paths = []
    message_paths = []

    sorted_upsides = sorted(upsides.items(), key=lambda x: x[1], reverse=True)
    for ticker, upside in sorted_upsides[:10]:
        print(f"{ticker}\n    Upside: {upside:.2%}\n    PEG Ratio: {peg_ratios[ticker]:.2f}\n    Fair Value: {fair_values[ticker]:.2f}\n    One Year Estimate: {one_year_estimates[ticker]:.2f}\n")
        plot_paths.append(all_plot_with_ta_paths[ticker])
        plot_paths.append(all_plot_paths[ticker])
        message_paths.append(all_message_paths[ticker])

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(plot_paths, message_paths, application))
