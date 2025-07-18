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


def chunk_list(lst, chunk_size):
    for list_index in range(0, len(lst), chunk_size):
        yield lst[list_index:list_index + chunk_size]


def has_buy_signal(dictionary):
    return (
        dictionary[DictionaryKeys.too_short] is False
        and (
            dictionary[DictionaryKeys.peg_ratio_too_high] is False
            and dictionary[DictionaryKeys.not_52w_low] is False
        )
        # and dictionary[DictionaryKeys.not_52w_low] is False
        and dictionary[DictionaryKeys.growth_too_low] is False
        and dictionary[DictionaryKeys.price_target_too_low] is False
        and dictionary[DictionaryKeys.too_expensive] is False
    )


def analyze(df, ticker, future=250, full=False):
    dictionary = {
        DictionaryKeys.too_short: False,
        DictionaryKeys.peg_ratio_too_high: False,
        DictionaryKeys.growth_too_low: False,
        DictionaryKeys.not_52w_low: False,
        DictionaryKeys.price_target_too_low: False,
        DictionaryKeys.too_expensive: False,
    }

    is_stock = not ticker_service.is_index(ticker) and not ticker_service.is_crypto(ticker) and not ticker_service.is_future(ticker)

    if len(df) < 2500:
        dictionary[DictionaryKeys.too_short] = True

    if is_stock:
        peg_ratio = yfinance_service.get_peg_ratio(ticker)
        if peg_ratio is None or peg_ratio > 1.0:
            dictionary[DictionaryKeys.peg_ratio_too_high] = True

        price_target = yfinance_service.get_price_target(ticker)
        if price_target is None or price_target <= df[P.H.value].iat[-1]:
            dictionary[DictionaryKeys.price_target_too_low] = True

        pe_ratio = yfinance_service.get_pe_ratio(ticker)
    else:
        peg_ratio = None
        price_target = None
        pe_ratio = None

    # df = regression_utility.add_growths(df, future=future)
    window = len(df) // 2
    df = regression_utility.add_window_growths(df, window=window, future=future)

    if df['Growth (High)'].iat[-1 - future] > df['Growth Lower (Low)'].iat[-1]:
        dictionary[DictionaryKeys.growth_too_low] = True

    if df[P.H.value].iat[-1 - future] > df['Growth Lower (Low)'].iat[-1 - future]:
        dictionary[DictionaryKeys.too_expensive] = True

    if df[P.L.value].iat[-1 - future] >= min(df[P.H.value].iloc[-1 - 2 * future:]):
        dictionary[DictionaryKeys.not_52w_low] = True

    # if not full and any(dictionary.values()):
    if not full and not has_buy_signal(dictionary):
        return dictionary, None

    name = yfinance_service.get_name(ticker=ticker)

    if price_target is not None or peg_ratio is not None or pe_ratio is not None:
        name += ' ('
        if price_target is not None:
            name += f'PT: {price_target} / '
        if peg_ratio is not None:
            name += f'PEG: {peg_ratio} / '
        if pe_ratio is not None:
            name += f'PE: {pe_ratio} / '
        name = name[:-3] + ')'

    plot_path = plot_utility.plot_bands_by_labels(
        df=df.iloc[-window-future:],
        ticker=ticker,
        title=name,
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
    tickers = ticker_service.get_all_tickers()
    # tickers = ['GOOGL']
    # tickers = ticker_service.get_nasdaq_100_tickers()

    too_short = 0
    peg_ratio_too_high = 0
    price_target_too_low = 0
    growth_too_low = 0
    too_expensive = 0
    not_52w_low = 0
    undervalued = 0

    plot_paths = []
    message_paths = []

    # future = 250

    chunk_size = 100
    for i, ticker_chunk in enumerate(chunk_list(tickers, chunk_size)):
        print(f'Processing chunk {i + 1} of {len(tickers) // chunk_size + 1}')

        # if i != 0:
            # sleep(10.0 * len(ticker_chunk))
            # sleep(len(ticker_chunk))

        df = yf.download(
            ticker_chunk,
            period='10y',
            interval='1d',
            group_by='ticker',
        )

        for ticker in tqdm(ticker_chunk):
            ticker_df = yfinance_service.extract_ticker_df(df=df, ticker=ticker)

            future = len(ticker_df) // 10

            try:
                dictionary, plot_path = analyze(df=ticker_df, ticker=ticker, future=future)
            except Exception as e:
                print(f'Error processing {ticker}: {e}')
                continue

            if dictionary[DictionaryKeys.too_short]:
                too_short += 1
            if dictionary[DictionaryKeys.peg_ratio_too_high]:
                peg_ratio_too_high += 1
            if dictionary[DictionaryKeys.price_target_too_low]:
                price_target_too_low += 1
            if dictionary[DictionaryKeys.growth_too_low]:
                growth_too_low += 1
            if dictionary[DictionaryKeys.too_expensive]:
                too_expensive += 1
            if dictionary[DictionaryKeys.not_52w_low]:
                not_52w_low += 1

            if plot_path is None:
                continue

            plot_paths.append(plot_path)
            undervalued += 1

    print(f'Too short: {too_short}')
    print(f'PEG ratio too high: {peg_ratio_too_high}')
    print(f'Price target too low: {price_target_too_low}')
    print(f'Growth too low: {growth_too_low}')
    print(f'Too expensive: {too_expensive}')
    print(f'Total tickers: {len(tickers)}')
    print(f'Undervalued: {undervalued}')

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(plot_paths, message_paths, application))
