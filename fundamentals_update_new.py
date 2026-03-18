import argparse
import asyncio
import time
import traceback
from typing import Dict

import yfinance as yf
from tqdm import tqdm

from alchemy import get_alchemy_scores, check_investment_rule
from constants import DictionaryKeysNew, UndervaluedKey, CommonDictionaryKey, TechnicalsKeys, GrowthKeys
from message_utility import get_message_by_dictionary_new, human_format, round_up
from pe_utility import update_pe_ratios
from plot_utility import plot_bands_by_labels_with_ta
from regression_utility import add_close_window_growths
from ta_utility import add_rsi
from telegram_service import get_application, send_plots, send_message_to_first
from ticker_service import get_all_tickers, is_crypto, is_stock, chunk_list, get_s_p_500_tickers
from yfinance_service import extract_ticker_df, get_pe_ratio_from_info, get_peg_ratio_from_info, \
    get_ev_to_ebitda_from_info, get_industry_from_info, get_price_target, P, get_name_from_info, \
    get_market_cap_from_info, get_recommendation_from_info


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

    dictionary, plot_path, _ = analyze(df=ticker_df, ticker=ticker, future=future, full=True, pe_ratios=pe_ratios)

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
    df = add_rsi(df)
    try:
        rsi = df[TechnicalsKeys.rsi.value].iat[-1] <= 100.0 / 3.0
    except:
        rsi = False
    if not rsi:
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
    price_target_growth = min(
        df[GrowthKeys.growth_lower.value].iat[-1],
        df[P.C.value].iat[today_index] * (1.0 + growth / 100.0),
    )
    if growth < 0.0:
        dictionary[DictionaryKeysNew.no_growth] = True

    # no_fundamentals
    yf_ticker = yf.Ticker(ticker)
    info = yf_ticker.info
    if is_stock(ticker):
        passes_inv_rule, _ = check_investment_rule(yf_ticker.balance_sheet, yf_ticker.financials)
        pe_ratio = get_pe_ratio_from_info(info)
        peg_ratio = get_peg_ratio_from_info(info)
        ev_to_ebitda = get_ev_to_ebitda_from_info(info)
        industry = get_industry_from_info(info)
        industry_pe_ratio = pe_ratios.get(industry) or pe_ratios.get('S&P 500') or 19.38
        price_target = get_price_target(ticker, low=True)
        market_cap = get_market_cap_from_info(info)
        recommendation = get_recommendation_from_info(info)
        score = get_alchemy_scores(yf_ticker, info).get('score')
        print(f'[{ticker}] recommendation={recommendation}, score={score}, price_target={price_target}, peg_ratio={peg_ratio}, pe_ratio={pe_ratio}, ev_to_ebitda={ev_to_ebitda}')
        if recommendation is None or 'BUY' not in recommendation.upper():
            print(f'[{ticker}] no_fundamentals: recommendation={recommendation}')
            dictionary[DictionaryKeysNew.no_fundamentals] = True
        if not passes_inv_rule:
            score = 0.0
        if score <= 0.0:
            print(f'[{ticker}] no_fundamentals: score={score}')
            dictionary[DictionaryKeysNew.no_fundamentals] = True
        if price_target is None:
            print(f'[{ticker}] no_fundamentals: price_target is None')
            dictionary[DictionaryKeysNew.no_fundamentals] = True
            price_target = price_target_growth
            value = df[GrowthKeys.growth.value].iat[today_index]
        else:
            value = min(price_target / (growth / 100.0 + 1.0), df[GrowthKeys.growth.value].iat[today_index])
            growth = min(
                growth,
                get_growth(
                    df[P.C.value].iat[today_index],
                    price_target,
                )
            )
            price_target = min(price_target, price_target_growth, value)
        if peg_ratio is None:
            print(f'[{ticker}] no_fundamentals: peg_ratio is None')
            dictionary[DictionaryKeysNew.no_fundamentals] = True
        else:
            if peg_ratio != 0 and pe_ratio is not None:
                growth = min(pe_ratio / peg_ratio, growth)
        if (ev_to_ebitda is None and pe_ratio is None) or growth is None:
            print(f'[{ticker}] no_fundamentals: ev_to_ebitda={ev_to_ebitda}, pe_ratio={pe_ratio}, growth={growth}')
            dictionary[DictionaryKeysNew.no_fundamentals] = True
            ev_to_ebitda_to_growth = None
        else:
            if growth > 0.0:
                if ev_to_ebitda is None:
                    ev_to_ebitda_to_growth = None
                else:
                    ev_to_ebitda_to_growth = ev_to_ebitda / growth
                if pe_ratio is not None:
                    if peg_ratio is not None:
                        peg_ratio = max(peg_ratio, pe_ratio / growth)
                    else:
                        peg_ratio = pe_ratio / growth
                if peg_ratio is None and ev_to_ebitda_to_growth is None:
                    print(f'[{ticker}] no_fundamentals: peg_ratio and ev_to_ebitda_to_growth are both None')
                    dictionary[DictionaryKeysNew.no_fundamentals] = True
                elif peg_ratio is None and ev_to_ebitda_to_growth is not None:
                    if ev_to_ebitda_to_growth > 1.0 or ev_to_ebitda_to_growth < 0.0:
                        print(f'[{ticker}] no_fundamentals: ev_to_ebitda_to_growth={ev_to_ebitda_to_growth} out of range')
                        dictionary[DictionaryKeysNew.no_fundamentals] = True
                elif ev_to_ebitda_to_growth is None and peg_ratio is not None:
                    if peg_ratio > 1.0 or peg_ratio < 0.0:
                        print(f'[{ticker}] no_fundamentals: peg_ratio={peg_ratio} out of range')
                        dictionary[DictionaryKeysNew.no_fundamentals] = True
                elif (ev_to_ebitda_to_growth > 1.0 or ev_to_ebitda_to_growth < 0.0) and (
                        peg_ratio > 1.0 or peg_ratio < 0.0):
                    print(f'[{ticker}] no_fundamentals: ev_to_ebitda_to_growth={ev_to_ebitda_to_growth}, peg_ratio={peg_ratio} both out of range')
                    dictionary[DictionaryKeysNew.no_fundamentals] = True
            else:
                ev_to_ebitda_to_growth = None
                if peg_ratio is not None:
                    if peg_ratio > 1.0 or peg_ratio < 0.0:
                        print(f'[{ticker}] no_fundamentals: growth<=0 and peg_ratio={peg_ratio} out of range')
                        dictionary[DictionaryKeysNew.no_fundamentals] = True
    else:
        market_cap = None
        score = None
        pe_ratio = None
        peg_ratio = None
        ev_to_ebitda = None
        industry_pe_ratio = None
        price_target = price_target_growth
        value = df[GrowthKeys.growth_lower.value].iat[today_index]
        ev_to_ebitda_to_growth = None

    # too_expensive
    if value < df[P.C.value].iat[today_index]:
        dictionary[DictionaryKeysNew.too_expensive] = True

    if not full and not has_buy_signal(dictionary):
        return dictionary, None, None

    name = get_name_from_info(info=info, ticker=ticker, industry_pe_ratio=industry_pe_ratio)
    subtitle = None

    if market_cap is not None or price_target is not None or peg_ratio is not None or pe_ratio is not None or ev_to_ebitda is not None:
        subtitle = ''
        if market_cap is not None:
            subtitle += f'MC: {human_format(market_cap)} - '
        if value is not None:
            subtitle += f'V: {human_format(value)} - '
        if price_target is not None:
            subtitle += f'PT: {human_format(price_target)} - '
        if peg_ratio is not None:
            subtitle += f'PEG: {round_up(peg_ratio)} - '
        if pe_ratio is not None:
            subtitle += f'P/E: {round_up(pe_ratio)} - '
        if ev_to_ebitda is not None:
            subtitle += f'EV/EBITDA: {round_up(ev_to_ebitda)}'
            if ev_to_ebitda_to_growth is not None:
                subtitle += f' ({round_up(ev_to_ebitda_to_growth)})'
            subtitle += ' - '
        if score is not None:
            subtitle += f'S: {human_format(score * 10000.0)} - '
        subtitle = subtitle[:-3]

    plot_path = plot_bands_by_labels_with_ta(
        df=df.iloc[-future - future:-future],
        ticker=ticker,
        title=name,
        subtitle=subtitle,
        labels=[
            GrowthKeys.growth_upper.value,
            GrowthKeys.growth.value,
            GrowthKeys.growth_lower.value,
        ],
        yscale='linear',
        # today=today_index,
        close_only=True,
        sma_labels=[
            # f'{TechnicalsKeys.ema.value}{ema_window_long}',
            # f'{TechnicalsKeys.ema.value}{ema_window_short}',
            # f'{TechnicalsKeys.sma.value}{sma_window_long}',
            # f'{TechnicalsKeys.sma.value}{sma_window_short}',
        ],
    )

    return dictionary, plot_path, score


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
        return None, None, None


def process_chunk(tickers, pe_ratios):
    df = yf.download(
        tickers=tickers,
        period='10y',
        interval='1d',
        group_by='ticker',
        repair=True,
    )

    indicator_counts = initialize_indicator_counts()

    messages = []
    plot_paths = []
    scores = []

    for ticker in tqdm(tickers):
        dictionary, plot_path, score = process_ticker(
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
        scores.append(score)

    return messages, plot_paths, scores, indicator_counts


def initialize_indicator_counts() -> Dict[CommonDictionaryKey, int]:
    indicator_counts: Dict[CommonDictionaryKey, int] = {UndervaluedKey.undervalued: 0}
    for key in DictionaryKeysNew:
        indicator_counts[key] = 0
    return indicator_counts


def main():
    parser = argparse.ArgumentParser(description='Send plots to Telegram subscribers.')
    parser.add_argument('--all', action='store_true', help='Send plots to all subscribers')
    args = parser.parse_args()

    # tickers = get_all_tickers()
    tickers = get_s_p_500_tickers()

    messages = []
    plot_paths = []
    scores = []
    indicator_counts = initialize_indicator_counts()

    pe_ratios = update_pe_ratios()

    chunk_size = 100

    for i, ticker_chunk in enumerate(chunk_list(tickers, chunk_size)):
        print(f'Processing chunk {i + 1} of {len(tickers) // chunk_size + 1}')
        if i > 0:
            time.sleep(chunk_size)

        messages_chunk, plot_paths_chunk, scores_chunk, indicator_counts_chunk = process_chunk(
            tickers=ticker_chunk,
            pe_ratios=pe_ratios,
        )
        messages.extend(messages_chunk)
        plot_paths.extend(plot_paths_chunk)
        scores.extend(scores_chunk)
        for key in DictionaryKeysNew:
            indicator_counts[key] += indicator_counts_chunk[key]

    # Sort by score descending; entries with None score come last
    sorted_items = sorted(
        zip(messages, plot_paths, scores),
        key=lambda x: (x[2] is None, -(x[2] if x[2] is not None else 0)),
    )
    if sorted_items:
        m, p, s = zip(*sorted_items)
        messages, plot_paths, scores = list(m), list(p), list(s)

    for key in DictionaryKeysNew:
        print(f'{key.value}: {indicator_counts[key]}')
    print(f'Total tickers: {len(tickers)}')
    print(f'{UndervaluedKey.undervalued.value}: {len(plot_paths)}')
    for message in messages:
        print(f'\n{message}')

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
