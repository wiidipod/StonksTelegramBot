import asyncio
from tqdm import tqdm
import plot_utility
import regression_utility
import ta_utility
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
from ticker_service import is_stock, is_crypto
from ta_utility import has_technicals
import pe_utility
import pandas as pd
from bisect import bisect_left
import retry_utility


def get_peg_ratio(df, labels, one_year, pe_ratio):
    peg_ratios = []
    for label in labels:
        growth_rate = df[label].iat[-1] / df[label].iat[-1 - one_year] - 1.0
        peg_ratio = pe_ratio / (growth_rate * 100.0)
        peg_ratios.append(peg_ratio)
    # growth_rate_5y = df[f'{add_string}Growth'].iat[-1] / df[f'{add_string}Growth'].iat[-1 - one_year] - 1.0
    # growth_rate_10y = df['Growth'].iat[-1] / df['Growth'].iat[-1 - one_year] - 1.0
    # peg_ratio_5y = pe_ratio / (growth_rate_5y * 100.0)
    # peg_ratio_10y = pe_ratio / (growth_rate_10y * 100.0)
    return min(peg_ratios)


def get_plot_path_and_message_for(ticker, period='10y', pe_ratios=None):
    if pe_ratios is None:
        pe_ratios = {}

    def _download_data():
        return yf.download(
            [ticker],
            period=period,
            interval='1d',
            group_by='ticker',
        )

    df = retry_utility.retry_data_fetch(_download_data)
    ticker_df = yfinance_service.extract_ticker_df(df=df, ticker=ticker)

    future = len(ticker_df) // 10

    dictionary, plot_path = analyze(df=ticker_df, ticker=ticker, future=future, full=True, pe_ratios=pe_ratios)

    message = message_utility.get_message_by_dictionary(dictionary=dictionary, ticker=ticker)

    return plot_path, message


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
            and dictionary[DictionaryKeys.no_technicals] is False
            and dictionary[DictionaryKeys.pe_ratio_too_high] is False
    )


def analyze(df, ticker, future=250, full=False, pe_ratios=None):
    if pe_ratios is None:
        pe_ratios = {}

    dictionary = {
        DictionaryKeys.too_short: False,
        DictionaryKeys.peg_ratio_too_high: False,
        DictionaryKeys.growth_too_low: False,
        DictionaryKeys.price_target_too_low: False,
        DictionaryKeys.too_expensive: False,
        DictionaryKeys.no_technicals: False,
        DictionaryKeys.pe_ratio_too_high: False,
    }

    if len(df) <= 2500:
        dictionary[DictionaryKeys.too_short] = True

    df = ta_utility.add_rsi(df)
    df = ta_utility.add_macd(df)
    # df = ta_utility.add_sma(df, window=200)
    try:
        macd = df["MACD Diff"].iat[-1] > df["MACD Diff"].iat[-2] or df["MACD Diff"].iat[-1] > 0.0
    except:
        macd = None
    try:
        rsi = df["RSI"].iat[-1]
    except:
        rsi = None
    # if macd is not None and rsi is not None:
    #     if (macd < 0.0 and rsi > 30.0) or rsi > 70.0:
    #         dictionary[DictionaryKeys.no_technicals] = True
    # else:
    #     dictionary[DictionaryKeys.no_technicals] = True
    if macd is not None and rsi is not None:
        # if (not macd and rsi > 30.0) or rsi > 70.0:
        if not macd or rsi > 70.0:
            dictionary[DictionaryKeys.no_technicals] = True
    else:
        dictionary[DictionaryKeys.no_technicals] = True

    if is_stock(ticker):
        pe_ratio = yfinance_service.get_pe_ratio(ticker)
        peg_ratio = yfinance_service.get_peg_ratio(ticker)
        industry = yfinance_service.get_industry(ticker)
        industry_pe_ratio = pe_ratios.get(industry) or pe_ratios.get('S&P 500') or 19.38
        price_target_low = yfinance_service.get_price_target(ticker, low=True)
        price_target_high = yfinance_service.get_price_target(ticker, low=False)
        if price_target_low is None:
            dictionary[DictionaryKeys.price_target_too_low] = True
    else:
        peg_ratio = None
        price_target_low = None
        price_target_high = None
        pe_ratio = None
        industry_pe_ratio = None

    window = len(df) - 1
    # window = len(df) // 2
    # add_string_5y = '5y '
    # df = regression_utility.add_window_growths(df, window=window, future=future)
    df = regression_utility.add_close_window_growths(
        df,
        window=window,
        future=future,
        is_crypto=is_crypto(ticker)
        # add_full_length_growth=True,
        # add_string=add_string_5y
    )

    if is_stock(ticker):
        if pe_ratio is not None:
            if peg_ratio is None:
                peg_ratio = get_peg_ratio(df, labels=["Growth"], one_year=future, pe_ratio=pe_ratio)
            else:
                peg_ratio = max(peg_ratio, get_peg_ratio(df, labels=["Growth"], one_year=future, pe_ratio=pe_ratio))
        else:
            dictionary[DictionaryKeys.pe_ratio_too_high] = True

        if peg_ratio is None:
            dictionary[DictionaryKeys.peg_ratio_too_high] = True
        elif peg_ratio > 1.0:
            dictionary[DictionaryKeys.peg_ratio_too_high] = True


        # if peg_ratio is None and (pe_ratio is None or industry_pe_ratio is None):
        #     dictionary[DictionaryKeys.peg_ratio_too_high] = True
        #     dictionary[DictionaryKeys.pe_ratio_too_high] = True
        # elif peg_ratio is not None and pe_ratio is not None and industry_pe_ratio is not None:
        #     if peg_ratio > 2.0 and pe_ratio > 2.0 * industry_pe_ratio:
        #         dictionary[DictionaryKeys.peg_ratio_too_high] = True
        #         dictionary[DictionaryKeys.pe_ratio_too_high] = True
        #     elif peg_ratio > 1.0 and pe_ratio > 2.0 * industry_pe_ratio:
        #         dictionary[DictionaryKeys.pe_ratio_too_high] = True
        #     elif peg_ratio > 2.0 and pe_ratio > industry_pe_ratio:
        #         dictionary[DictionaryKeys.peg_ratio_too_high] = True
        # elif pe_ratio is not None and industry_pe_ratio is not None:
        #     if pe_ratio > 2.0 * industry_pe_ratio:
        #         dictionary[DictionaryKeys.pe_ratio_too_high] = True
        # elif peg_ratio is not None:
        #     if peg_ratio > 2.0:
        #         dictionary[DictionaryKeys.peg_ratio_too_high] = True

    # days_to_outperform_volatility = bisect_left(df['Growth Lower'].to_numpy(), df['Growth Upper'].iat[0])

    if (
        # 10y regression not beating volatility in 5y
        # df['Growth Upper'].iat[-1 - window - future] > df['Growth Lower'].iat[-1 - future]
        # 10y regression not growing
        df['Growth Lower'].iat[-1 - future] > df['Growth Lower'].iat[-1]
        # 5y regression not growing
        # or df[f'{add_string_5y}Growth'].iat[-1 - future] > df[f'{add_string_5y}Growth'].iat[-1]
        # 5y regression not beating volatility in 5y
        # or df[f'{add_string_5y}Growth Upper'].iat[-1 - future - window] > df[f'{add_string_5y}Growth Lower'].iat[-1 - future]
        # or days_to_outperform_volatility >= len(df) - future
    ):
        dictionary[DictionaryKeys.growth_too_low] = True

    if (
        # price not below lower 10y regression
        df[P.C.value].iat[-1 - future] > df['Growth Lower'].iat[-1 - future]
        # price not below 10y regression
        # df [P.C.value].iat[-1 - future] > df['Growth'].iat[-1 - future]
        # price not below 5y regression
        # or df[P.C.value].iat[-1 - future] > df[f'{add_string_5y}Growth'].iat[-1 - future]
        # price not below lower 5y regression
        # or df[P.C.value].iat[-1 - future] > df[f'{add_string_5y}Growth Lower'].iat[-1 - future]
        # price not low for volatility and growth
        # or min(df[P.C.value].iloc[-1-future-26:-future]) > min(df[P.C.value].iloc[-1-future-days_to_outperform_volatility:-1-future-26])
    ):
        dictionary[DictionaryKeys.too_expensive] = True

    if price_target_low is None:
        # price_target_low = min(df['Growth Lower'].iat[-1], df[f'{add_string_5y}Growth Lower'].iat[-1])
        price_target_low = df['Growth Lower'].iat[-1]
    else:
        # price_target_low = min(price_target_low, df['Growth Lower'].iat[-1], df[f'{add_string_5y}Growth Lower'].iat[-1])
        price_target_low = min(price_target_low, df['Growth Lower'].iat[-1])

    if price_target_high is None:
        # price_target_high = max(df['Growth Upper'].iat[-1], df[f'{add_string_5y}Growth Upper'].iat[-1])
        price_target_high = df['Growth Upper'].iat[-1]
    else:
        # price_target_high = max(price_target_high, df['Growth Upper'].iat[-1], df[f'{add_string_5y}Growth Upper'].iat[-1])
        price_target_high = max(price_target_high, df['Growth Upper'].iat[-1])

    # if 0.9 * price_target_low <= df[P.H.value].iat[-1 - future]:
    if price_target_low < 1.1 * df[P.C.value].iat[-1 - future]:
        dictionary[DictionaryKeys.price_target_too_low] = True

    if not full and not has_buy_signal(dictionary):
        return dictionary, None

    name = yfinance_service.get_name(ticker=ticker, industry_pe_ratio=industry_pe_ratio)
    ev_to_ebitda = yfinance_service.get_ev_to_ebitda(ticker)
    subtitle = None

    if price_target_low is not None or peg_ratio is not None or pe_ratio is not None or ev_to_ebitda is not None:
        subtitle = ''
        if price_target_low is not None:
            # relative_offset = ((df[P.C.value].iat[-1 - future] / price_target_low) - 1.0) * 100.0
            # subtitle += f'PT: {round_down(price_target_low)} ({round_down(relative_offset)}%) / {round_up(price_target_high)} - '-
            subtitle += f'PT: {round_down(price_target_low)} / {round_up(price_target_high)} - '
        if peg_ratio is not None:
            subtitle += f'PEG: {round_up(peg_ratio)} - '
        if pe_ratio is not None:
            subtitle += f'P/E: {round_up(pe_ratio)} - '
        if ev_to_ebitda is not None:
            subtitle += f'EV/EBITDA: {round_up(ev_to_ebitda)} - '
        # if macd is not None:
        #     subtitle += f'MACD Diff: {round_down(macd)} - '
        # if rsi is not None:
        #     subtitle += f'RSI: {round_up(rsi)} - '
        subtitle = subtitle[:-3]

    plot_path = plot_utility.plot_bands_by_labels(
        df=df,  # .iloc[window:],
        ticker=ticker,
        title=name,
        subtitle=subtitle,
        labels=[
            'Growth',
            'Growth Lower',
            'Growth Upper',
            # f'{add_string_5y}Growth',
            # f'{add_string_5y}Growth Lower',
            # f'{add_string_5y}Growth Upper',
        ],
        yscale='linear',
        today=-1-future,
        close_only=True,
        # sma_label=f'SMA-200',
    )

    return dictionary, plot_path


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description='Send plots to Telegram subscribers.')
        parser.add_argument('--all', action='store_true', help='Send plots to all subscribers')
        args = parser.parse_args()

        tickers = ticker_service.get_all_tickers()
        # tickers = ticker_service.get_s_p_500_tickers()
        # tickers = ticker_service.get_dow_jones_tickers()
        # tickers = ['AAPL']

        too_short = 0
        peg_ratio_too_high = 0
        price_target_too_low = 0
        growth_too_low = 0
        too_expensive = 0
        no_momentum = 0
        pe_ratio_too_high = 0
        undervalued = 0

        plot_paths = []

        main_pe_ratios = pe_utility.update_pe_ratios()

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
                try:
                    ticker_df_main = yfinance_service.extract_ticker_df(df=df_main, ticker=ticker_main)

                    future_main = len(ticker_df_main) // 10

                    dictionary_main, plot_path_main = analyze(df=ticker_df_main, ticker=ticker_main, future=future_main, pe_ratios=main_pe_ratios)
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
                if dictionary_main[DictionaryKeys.no_technicals]:
                    no_momentum += 1
                if dictionary_main[DictionaryKeys.pe_ratio_too_high]:
                    pe_ratio_too_high += 1

                if plot_path_main is None:
                    continue

                plot_paths.append(plot_path_main)
                undervalued += 1

        print(f'Too short: {too_short}')
        print(f'PEG ratio too high: {peg_ratio_too_high}')
        print(f'Price target too low: {price_target_too_low}')
        print(f'Growth too low: {growth_too_low}')
        print(f'Too expensive: {too_expensive}')
        print(f'No technicals: {no_momentum}')
        print(f'PE ratio too high: {pe_ratio_too_high}')
        print(f'Total tickers: {len(tickers)}')
        print(f'Undervalued: {undervalued}')

        application = telegram_service.get_application()
        if args.all:
            asyncio.run(telegram_service.send_plots_to_all(plot_paths, application))
        else:
            asyncio.run(telegram_service.send_plots_to_first(plot_paths, application))
    except Exception as e:
        import traceback
        error_message = f"Error in fundamentals_update:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(error_message)
        try:
            application = telegram_service.get_application()
            asyncio.run(telegram_service.send_message_to_first(error_message, application))
        except Exception as notification_error:
            print(f"Failed to send error notification: {notification_error}")
