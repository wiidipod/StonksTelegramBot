import asyncio
from time import sleep
from tqdm import tqdm
import plot_utility
import regression_utility
import telegram_service
import ticker_service
from yfinance_service import P
import yfinance as yf
import yfinance_service
from constants import dictionary_keys


def chunk_list(lst, chunk_size):
    for list_index in range(0, len(lst), chunk_size):
        yield lst[list_index:list_index + chunk_size]


def analyze(df, ticker, future=250, full=False):
    dictionary = {
        dictionary_keys.too_short: False,
        dictionary_keys.peg_ratio_too_high: False,
        dictionary_keys.weak_growth: False,
        dictionary_keys.not_cheap: False,
    }

    if len(df) < 2500:
        dictionary[dictionary_keys.too_short] = True

    peg_ratio = yfinance_service.get_peg_ratio(ticker)
    if peg_ratio is None or peg_ratio > 1.0:
        dictionary[dictionary_keys.peg_ratio_too_high] = True

    df = regression_utility.add_growths(df, future=future)

    if df['Growth (High)'].iat[-1 - future] > df['Growth Lower (Low)'].iat[-1]:
        dictionary[dictionary_keys.weak_growth] = True

    if df[P.H.value].iat[-1 - future] > df['Growth Lower (Low)'].iat[-1 - future]:
        dictionary[dictionary_keys.not_cheap] = True

    if not full and any(dictionary.values()):
        return dictionary, None

    name = yfinance_service.get_name(ticker=ticker)
    name += f' (PEG: {peg_ratio})'

    plot_path = plot_utility.plot_bands_by_labels(
        df=df,
        ticker=ticker,
        title=name,
        labels=[
            'Growth',
            'Growth Lower',
            'Growth Upper',
        ],
        yscale='log',
        today=-1-future,
    )

    return dictionary, plot_path


if __name__ == '__main__':
    # tickers = ticker_service.get_all_tickers()
    tickers = ['GOOGL', 'GOOG']

    too_short = 0
    peg_ratio_too_high = 0
    weak_growth = 0
    not_cheap = 0

    plot_paths = []
    message_paths = []

    future = 250

    chunk_size = 100
    for i, ticker_chunk in enumerate(chunk_list(tickers, chunk_size)):
        print(f'Processing chunk {i + 1} of {len(tickers) // chunk_size + 1}')

        if i != 0:
            sleep(10.0 * len(ticker_chunk))

        df = yf.download(
            ticker_chunk,
            period='10y',
            interval='1d',
            group_by='ticker',
        )

        for ticker in tqdm(ticker_chunk):
            ticker_df = yfinance_service.extract_ticker_df(df=df, ticker=ticker)
            ticker_df = ticker_df.iloc[:-1]

            dictionary, plot_path = analyze(df=ticker_df, ticker=ticker, future=future)

            if dictionary[dictionary_keys.too_short]:
                too_short += 1
            if dictionary[dictionary_keys.peg_ratio_too_high]:
                peg_ratio_too_high += 1
            if dictionary[dictionary_keys.weak_growth]:
                weak_growth += 1
            if dictionary[dictionary_keys.not_cheap]:
                not_cheap += 1

            if plot_path is None:
                continue

            plot_paths.append(plot_path)

    print(f'Tickers too short: {too_short}')
    print(f'PEG ratio too high: {peg_ratio_too_high}')
    print(f'Weak growth: {weak_growth}')
    print(f'Not cheap: {not_cheap}')
    print(f'Total tickers: {len(tickers)}')

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(plot_paths, message_paths, application))
