import asyncio
from tqdm import tqdm
import plot_utility
import regression_utility
import telegram_service
import ticker_service
from yfinance_service import P
import yfinance as yf
import yfinance_service
from constants import DictionaryKeys
import time
import argparse
from message_utility import round_down, round_up
import message_utility
from ticker_service import is_stock


def get_plot_and_message_paths_for(ticker):
    df = yf.download(
        [ticker],
        period='10y',
        interval='1d',
        group_by='ticker',
    )
    ticker_df = yfinance_service.extract_ticker_df(df=df, ticker=ticker)

    future = len(ticker_df) // 10

    dictionary, plot_path = analyze(df=ticker_df, ticker=ticker, future=future, full=True)

    message_path = message_utility.write_message_by_dictionary(dictionary=dictionary, ticker=ticker)

    return plot_path, message_path


def chunk_list(lst, chunk_size):
    for list_index in range(0, len(lst), chunk_size):
        yield lst[list_index:list_index + chunk_size]


def has_buy_signal(dictionary):
    return (
        dictionary[DictionaryKeys.too_short] is False
        and dictionary[DictionaryKeys.peg_ratio_too_high] is False
        and dictionary[DictionaryKeys.growth_too_low] is False
        and dictionary[DictionaryKeys.price_target_too_low] is False
        and dictionary[DictionaryKeys.too_expensive] is False
    )


def analyze(df, ticker, future=250, full=False):
    dictionary = {
        DictionaryKeys.too_short: False,
        DictionaryKeys.peg_ratio_too_high: False,
        DictionaryKeys.growth_too_low: False,
        DictionaryKeys.price_target_too_low: False,
        DictionaryKeys.too_expensive: False,
    }

    if len(df) <= 2500:
        dictionary[DictionaryKeys.too_short] = True

    if is_stock(ticker):
        peg_ratio = yfinance_service.get_peg_ratio(ticker)
        if peg_ratio is None or peg_ratio > 1.0:
            dictionary[DictionaryKeys.peg_ratio_too_high] = True

        price_target = yfinance_service.get_price_target(ticker)
        if price_target is None:
            dictionary[DictionaryKeys.price_target_too_low] = True

        pe_ratio = yfinance_service.get_pe_ratio(ticker)
    else:
        peg_ratio = None
        price_target = None
        pe_ratio = None

    window = len(df) - 1
    df = regression_utility.add_window_growths(df, window=window, future=future)

    if (
        df['Growth Upper (High)'].iat[-1 - future * 5] >= df['Growth Lower (Low)'].iat[-1]
    ):
        dictionary[DictionaryKeys.growth_too_low] = True

    if (
        df[P.H.value].iat[-1 - future] >= df['Growth Lower (Low)'].iat[-1 - future]
        or df[P.L.value].iat[-1 - future] >= min(df[P.H.value].iloc[-1 - future - len(df) // 10:-1 - future])
    ):
        dictionary[DictionaryKeys.too_expensive] = True

    if price_target is None:
        price_target = df['Growth Lower (Low)'].iat[-1]
    else:
        price_target = min(price_target, df['Growth Lower (Low)'].iat[-1])

    if 0.9 * price_target <= df[P.H.value].iat[-1 - future]:
        dictionary[DictionaryKeys.price_target_too_low] = True

    if not full and not has_buy_signal(dictionary):
        return dictionary, None

    name = yfinance_service.get_name(ticker=ticker)
    ev_to_ebitda = yfinance_service.get_ev_to_ebitda(ticker)
    subtitle = None

    if price_target is not None or peg_ratio is not None or pe_ratio is not None or ev_to_ebitda is not None:
        subtitle = ''
        if price_target is not None:
            relative_offset = ((df[P.H.value].iat[-1 - future] / price_target) - 1.0) * 100.0
            subtitle += f'PT: {round_down(price_target)} ({round_down(relative_offset)}%) - '
        if peg_ratio is not None:
            subtitle += f'PEG: {round_up(peg_ratio)} - '
        if pe_ratio is not None:
            subtitle += f'P/E: {round_up(pe_ratio)} - '
        if ev_to_ebitda is not None:
            subtitle += f'EV/EBITDA: {round_up(ev_to_ebitda)} - '
        subtitle = subtitle[:-3]

    plot_path = plot_utility.plot_bands_by_labels(
        df=df,
        ticker=ticker,
        title=name,
        subtitle=subtitle,
        labels=[
            'Growth',
            'Growth Lower',
            'Growth Upper',
        ],
        yscale='linear',
        today=-1-future,
    )

    return dictionary, plot_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send plots to Telegram subscribers.')
    parser.add_argument('--all', action='store_true', help='Send plots to all subscribers')
    args = parser.parse_args()

    tickers = ticker_service.get_all_tickers()

    too_short = 0
    peg_ratio_too_high = 0
    price_target_too_low = 0
    growth_too_low = 0
    too_expensive = 0
    undervalued = 0

    plot_paths = []

    chunk_size_main = 100
    for i, ticker_chunk in enumerate(chunk_list(tickers, chunk_size_main)):
        print(f'Processing chunk {i + 1} of {len(tickers) // chunk_size_main + 1}')

        if i > 0:
            time.sleep(chunk_size_main)

        df_main = yf.download(
            ticker_chunk,
            period='10y',
            interval='1d',
            group_by='ticker',
        )

        for ticker_main in tqdm(ticker_chunk):
            ticker_df_main = yfinance_service.extract_ticker_df(df=df_main, ticker=ticker_main)

            future_main = len(ticker_df_main) // 10

            try:
                dictionary_main, plot_path_main = analyze(df=ticker_df_main, ticker=ticker_main, future=future_main)
            except Exception as e:
                print(f'Error processing {ticker_main}: {e}')
                continue

            if dictionary_main[DictionaryKeys.too_short]:
                too_short += 1
            if dictionary_main[DictionaryKeys.peg_ratio_too_high]:
                peg_ratio_too_high += 1
            if dictionary_main[DictionaryKeys.price_target_too_low]:
                price_target_too_low += 1
            if dictionary_main[DictionaryKeys.growth_too_low]:
                growth_too_low += 1
            if dictionary_main[DictionaryKeys.too_expensive]:
                too_expensive += 1

            if plot_path_main is None:
                continue

            plot_paths.append(plot_path_main)
            undervalued += 1

    print(f'Too short: {too_short}')
    print(f'PEG ratio too high: {peg_ratio_too_high}')
    print(f'Price target too low: {price_target_too_low}')
    print(f'Growth too low: {growth_too_low}')
    print(f'Too expensive: {too_expensive}')
    print(f'Total tickers: {len(tickers)}')
    print(f'Undervalued: {undervalued}')

    application = telegram_service.get_application()
    if args.all:
        asyncio.run(telegram_service.send_plots_to_all(plot_paths, application))
    else:
        asyncio.run(telegram_service.send_plots_to_first(plot_paths, application))
