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
    for list_index in range(0, len(lst), chunk_size):
        yield lst[list_index:list_index + chunk_size]


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

    too_short = 0
    not_bullish = 0
    peg_ratio_too_high = 0
    no_growth = 0
    close_too_high = 0
    no_fair_value = 0
    one_year_estimate_too_low = 0
    upside_negative = 0

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
                too_short += 1
                continue

            technicals = ta_utility.get_technicals(close)
            bullish, rsi, rsi_sma, macd, macd_signal, macd_diff = technicals
            if not bullish and not backtest:
                not_bullish += 1
                continue

            peg_ratio = yfinance_service.get_peg_ratio(ticker)
            if peg_ratio is None or peg_ratio > 2.0 and not backtest:
                peg_ratio_too_high += 1
                continue

            growth, lower_growth, upper_growth, double_lower_growth, double_upper_growth = regression_utility.get_growths(close, future=future)
            if growth[-future] >= growth[-1]:
                no_growth += 1
                continue

            if lower_growth[-future] < close[-1]:
                close_too_high += 1
                continue

            fair_value = yfinance_service.get_fair_value(ticker, growth[:-future], backtest=backtest)
            if fair_value is None or fair_value <= 0.0:
                no_fair_value += 1
                continue

            one_year_estimate = min(growth[-1], fair_value)
            if one_year_estimate <= close[-1]:
                one_year_estimate_too_low += 1
                continue

            upside = one_year_estimate / close[-1] - 1.0
            if upside <= 0.0:
                upside_negative += 1
                continue

            fair_values[ticker] = fair_value
            upsides[ticker] = upside
            peg_ratios[ticker] = peg_ratio
            one_year_estimates[ticker] = one_year_estimate

            name = f'{yfinance_service.get_name(ticker)}'
            growths = [double_lower_growth, lower_growth, growth, upper_growth, double_upper_growth]

            plot_with_ta_path = plot_utility.plot_with_ta(
                ticker,
                name,
                close,
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
                ta_utility.get_sma(close),
                growths=growths,
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

    print(f'\n\nToo short: {too_short}')
    print(f'Not bullish: {not_bullish}')
    print(f'PEG ratio too high: {peg_ratio_too_high}')
    print(f'No growth: {no_growth}')
    print(f'Close too high: {close_too_high}')
    print(f'No fair value: {no_fair_value}')
    print(f'One year estimate too low: {one_year_estimate_too_low}')
    print(f'Upside negative: {upside_negative}')

    sorted_upsides = sorted(upsides.items(), key=lambda x: x[1], reverse=True)
    for ticker, upside in sorted_upsides[:10]:
        print(f"{ticker}\n    Upside: {upside:.2%}\n    PEG Ratio: {peg_ratios[ticker]:.2f}\n    Fair Value: {fair_values[ticker]:.2f}\n    One Year Estimate: {one_year_estimates[ticker]:.2f}\n")
        plot_paths.append(all_plot_with_ta_paths[ticker])
        plot_paths.append(all_plot_paths[ticker])
        message_paths.append(all_message_paths[ticker])

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(plot_paths, message_paths, application))
