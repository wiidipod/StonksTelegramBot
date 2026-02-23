import argparse
import time
import yfinance as yf
from tqdm import tqdm
import asyncio
import traceback
from typing import Dict

from ticker_service import get_all_tickers, is_crypto, is_stock, get_s_p_500_tickers
from pe_utility import update_pe_ratios
from yfinance_service import extract_ticker_df, get_pe_ratio_from_info, get_peg_ratio_from_info, \
    get_ev_to_ebitda_from_info, get_industry_from_info, get_price_target_from_info, P, get_name_from_info, \
    get_market_cap_from_info
from constants import DictionaryKeysNew, UndervaluedKey, CommonDictionaryKey, TechnicalsKeys, GrowthKeys
from message_utility import get_message_by_dictionary_new, round_down, human_format, human_format_from_string, round_up
from telegram_service import get_application, send_plots, send_message_to_first
from ta_utility import add_macd
from regression_utility import add_close_window_growths
from plot_utility import plot_bands_by_labels_with_ta


def get_growth(value_today, value_future):
    return (value_future / value_today - 1.0) * 100.0


def has_buy_signal(dictionary):
    return not any(dictionary[key] for key in DictionaryKeysNew)


def get_plot_path_and_message_for(ticker, period='10y', pe_ratios=None):
    if pe_ratios is None:
        pe_ratios = {}

    df = yf.download(
        [ticker],
        period=period,
        interval='1d',
        group_by='ticker',
        auto_adjust=True,
    )
    ticker_df = extract_ticker_df(df=df, ticker=ticker)

    # Check if the DataFrame is empty after extraction
    if ticker_df.empty:
        raise ValueError(f"No data available for ticker {ticker}")

    future = len(ticker_df) // 10

    dictionary, plot_path = analyze(df=ticker_df, ticker=ticker, future=future, full=True, pe_ratios=pe_ratios)

    message = get_message_by_dictionary_new(dictionary=dictionary, ticker=ticker)

    return plot_path, message


def analyze(df, ticker, future=250, full=False, pe_ratios=None):
    if pe_ratios is None:
        pe_ratios = {}

    dictionary = {}
    for key in DictionaryKeysNew:
        dictionary[key] = False

    # too_short
    if len(df) < 2500:
        dictionary[DictionaryKeysNew.too_short] = True

    # no_technicals
    df = add_macd(df)
    try:
        # macd = df[TechnicalsKeys.macd_diff.value].iat[-1] >= 0.0 >= df[TechnicalsKeys.macd_diff.value].iat[-2]
        # macd = df[TechnicalsKeys.macd_diff.value].iat[-1] >= 0.0
        macd = True
    except:
        macd = None
    if macd is not None:
        if not macd:
            dictionary[DictionaryKeysNew.no_technicals] = True
    else:
        dictionary[DictionaryKeysNew.no_technicals] = True

    # regression
    window = len(df) - 1
    today_index = -1 - future
    df = add_close_window_growths(
        df=df,
        window=window,
        future=future,
        is_crypto=is_crypto(ticker)
    )
    growth = get_growth(
        value_today=df[GrowthKeys.growth.value].iat[today_index],
        value_future=df[GrowthKeys.growth.value].iat[-1],
    )
    if growth < 0.0:
        dictionary[DictionaryKeysNew.no_growth] = True

    # no_fundamentals
    info = yf.Ticker(ticker).info
    if is_stock(ticker):
        pe_ratio = get_pe_ratio_from_info(info)
        peg_ratio = get_peg_ratio_from_info(info)
        ev_to_ebitda = get_ev_to_ebitda_from_info(info)
        industry = get_industry_from_info(info)
        industry_pe_ratio = pe_ratios.get(industry) or pe_ratios.get('S&P 500') or 19.38
        price_target = get_price_target_from_info(info, low=True)
        if price_target is None:
            dictionary[DictionaryKeysNew.no_fundamentals] = True
            price_target = df[GrowthKeys.growth_lower.value].iat[-1]
        else:
            growth = min(growth, get_growth(
                df[P.C.value].iat[today_index],
                price_target,
            ))
            price_target = min(price_target, df[GrowthKeys.growth_lower.value].iat[-1])
        if pe_ratio is None or peg_ratio is None:
            dictionary[DictionaryKeysNew.no_fundamentals] = True
        else:
            if peg_ratio != 0:
                growth = min(pe_ratio / peg_ratio, growth)
        if ev_to_ebitda is None:
            dictionary[DictionaryKeysNew.no_fundamentals] = True
            ev_to_ebitda_to_growth = None
        else:
            if growth != 0:
                ev_to_ebitda_to_growth = ev_to_ebitda / growth
                if ev_to_ebitda_to_growth > 1.0:
                    dictionary[DictionaryKeysNew.no_fundamentals] = True
            else:
                ev_to_ebitda_to_growth = None
                dictionary[DictionaryKeysNew.no_fundamentals] = True
    else:
        pe_ratio = None
        peg_ratio = None
        ev_to_ebitda = None
        industry_pe_ratio = None
        price_target = df[GrowthKeys.growth_lower.value].iat[-1]
        ev_to_ebitda_to_growth = None

    # too_expensive
    if min(price_target, df[GrowthKeys.growth.value].iat[today_index]) < df[P.C.value].iat[today_index]:
        dictionary[DictionaryKeysNew.too_expensive] = True

    if not full and not has_buy_signal(dictionary):
        return dictionary, None

    name = get_name_from_info(info=info, ticker=ticker, industry_pe_ratio=industry_pe_ratio)
    subtitle = None
    market_cap = get_market_cap_from_info(info)

    if market_cap is not None or price_target is not None or peg_ratio is not None or pe_ratio is not None or ev_to_ebitda is not None:
        subtitle = ''
        if market_cap is not None:
            subtitle += f'MC: {human_format(market_cap)} - '
        if price_target is not None:
            subtitle += f'PT: {human_format_from_string(round_down(price_target))} - '
        if peg_ratio is not None:
            subtitle += f'PEG: {round_up(peg_ratio)} - '
        if pe_ratio is not None:
            subtitle += f'P/E: {round_up(pe_ratio)} - '
        if ev_to_ebitda is not None:
            subtitle += f'EV/EBITDA: {round_up(ev_to_ebitda)}'
            if ev_to_ebitda_to_growth is not None:
                subtitle += f' ({round_up(ev_to_ebitda_to_growth)})'
            subtitle += ' - '
        subtitle = subtitle[:-3]

    plot_path = plot_bands_by_labels_with_ta(
        df=df,
        ticker=ticker,
        title=name,
        subtitle=subtitle,
        labels=[
            GrowthKeys.growth.value,
            GrowthKeys.growth_lower.value,
            GrowthKeys.growth_upper.value,
        ],
        yscale='linear',
        today=today_index,
        close_only=True,
    )

    return dictionary, plot_path


def chunk_list(lst, chunk_size):
    for list_index in range(0, len(lst), chunk_size):
        yield lst[list_index:list_index + chunk_size]


def process_ticker(df, ticker, pe_ratios):
    try:
        ticker_df = extract_ticker_df(
            df=df,
            ticker=ticker
        )

        future = len(ticker_df) // 10

        return analyze(
            df=ticker_df,
            ticker=ticker,
            future=future,
            pe_ratios=pe_ratios,
        )

    except Exception as e:
        print(f'Error processing {ticker}: {e}')
        return None, None


def process_chunk(tickers, pe_ratios):
    df = yf.download(
        tickers=tickers,
        period='10y',
        interval='1d',
        group_by='ticker',
    )

    indicator_counts = initialize_indicator_counts()

    messages = []
    plot_paths = []

    for ticker in tqdm(tickers):
        dictionary, plot_path = process_ticker(
            df=df,
            ticker=ticker,
            pe_ratios=pe_ratios
        )

        if dictionary is None:
            continue

        for key in DictionaryKeysNew:
            if dictionary[key]:
                indicator_counts[key] += 1

        if plot_path is None:
            continue

        message = get_message_by_dictionary_new(
            dictionary=dictionary,
            ticker=ticker,
        )
        messages.append(message)

        plot_paths.append(plot_path)

        indicator_counts[UndervaluedKey.undervalued] += 1

    return messages, plot_paths, indicator_counts


def initialize_indicator_counts() -> Dict[CommonDictionaryKey, int]:
    indicator_counts: Dict[CommonDictionaryKey, int] = {UndervaluedKey.undervalued: 0}
    for key in DictionaryKeysNew:
        indicator_counts[key] = 0
    return indicator_counts


def main():
    parser = argparse.ArgumentParser(description='Send plots to Telegram subscribers.')
    parser.add_argument('--all', action='store_true', help='Send plots to all subscribers')
    args = parser.parse_args()

    tickers = get_all_tickers()

    messages = []
    plot_paths = []
    indicator_counts = initialize_indicator_counts()

    pe_ratios = update_pe_ratios()

    chunk_size = 100

    for i, ticker_chunk in enumerate(chunk_list(tickers, chunk_size)):
        print(f'Processing chunk {i + 1} of {len(tickers) // chunk_size + 1}')
        if i > 0:
            time.sleep(chunk_size)

        messages_chunk, plot_paths_chunk, indicator_counts_chunk = process_chunk(
            tickers=ticker_chunk,
            pe_ratios=pe_ratios,
        )
        messages.extend(messages_chunk)
        plot_paths.extend(plot_paths_chunk)
        for key in DictionaryKeysNew:
            indicator_counts[key] += indicator_counts_chunk[key]

    for key in DictionaryKeysNew:
        print(f'{key.value}: {indicator_counts[key]}')
    print(f'Total tickers: {len(tickers)}')
    print(f'{UndervaluedKey.undervalued.value}: {indicator_counts[UndervaluedKey.undervalued]}')

    application = get_application()
    asyncio.run(send_plots(
        context=application,
        plot_paths=plot_paths,
        messages=messages,
        to_all=args.all,
    ))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        error_message = f"Error in fundamentals_update:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(error_message)
        try:
            asyncio.run(send_message_to_first(
                message=error_message,
                context=(get_application())
            ))
        except Exception as notification_error:
            print(f"Failed to send error notification: {notification_error}")
