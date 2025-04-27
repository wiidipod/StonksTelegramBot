import asyncio
from time import sleep
from tqdm import tqdm

import message_utility
import plot_utility
import regression_utility
import telegram_service
import ticker_service
from yfinance_service import P
import yfinance as yf

import yfinance_service


def chunk_list(lst, chunk_size):
    for list_index in range(0, len(lst), chunk_size):
        yield lst[list_index:list_index + chunk_size]


if __name__ == '__main__':
    tickers = ticker_service.get_all_tickers()
    # print(tickers)
    # tickers = ['ADI']
    # tickers = ['VOW.DE', 'VOW3.DE', 'WDAY']

    too_short = 0
    peg_ratio_too_high = 0
    weak_growth = 0
    not_cheap = 0
    no_fair_value = 0

    plot_paths = []
    message_paths = []

    future = 250

    chunk_size = 100
    for i, ticker_chunk in enumerate(chunk_list(tickers, chunk_size)):
        print(f'Processing chunk {i + 1} of {len(tickers) // chunk_size + 1}')

        if i != 0:
            sleep(len(ticker_chunk))

        df = yf.download(
            ticker_chunk,
            period='10y',
            interval='1d',
            group_by='ticker',
            # timeout=100.0,
        )

        # print(df.tail())
        # print(df.head())

        for ticker in tqdm(ticker_chunk):
        # for ticker in ticker_chunk:
            ticker_df = yfinance_service.extract_ticker_df(df=df, ticker=ticker)

            if len(ticker_df) < 2500:
                too_short += 1
                continue

            peg_ratio = yfinance_service.get_peg_ratio(ticker)
            if peg_ratio is None or peg_ratio > 1.0:
                peg_ratio_too_high += 1
                continue

            ticker_df = regression_utility.add_growths(ticker_df, future=future)
            # print(ticker_df['Growth Upper (High)'].iat[-1 - future])
            # print(ticker_df['Growth Lower (Low)'].iat[-1])
            # print(ticker_df['Growth Upper (High)'].iat[-1 - future] > ticker_df['Growth Lower (Low)'].iat[-1])

            if ticker_df['Growth (High)'].iat[-1 - future] > ticker_df['Growth Lower (Low)'].iat[-1]:
                weak_growth += 1
                # print(f'{ticker} has weak growth: {ticker_df["Growth Upper (High)"].iat[-1 - future]} > {ticker_df["Growth Lower (Low)"].iat[-1]}')
                continue

            if ticker_df[P.H.value].iat[-1 - future] > ticker_df['Growth Lower (Low)'].iat[-1 - future]:
                not_cheap += 1
                # print(f'{ticker} is not cheap: {ticker_df[P.H.value].iat[-1 - future]} > {ticker_df["Growth Lower (Low)"].iat[-1 - future]}')
                continue

            # fair_value = yfinance_service.get_fair_value(
            #     ticker=ticker,
            #     growth_1y=ticker_df['Growth (High)'].iloc[-1 - future:].tolist()
            # )
            # if fair_value is None or fair_value <= 0.0 or ticker_df[P.H.value].iat[-1 - future] > fair_value:
            #     no_fair_value += 1
                # print(f'{ticker} has no fair value: {ticker_df[P.H.value].iat[-1 - future]} > {fair_value}')
                # continue

            # ev_to_ebitda = yfinance_service.get_ev_to_ebitda(ticker)
            name = yfinance_service.get_name(ticker=ticker)  # + f' (EV/EBITDA: {ev_to_ebitda})'
            name += f' (PEG: {peg_ratio})'

            plot_path = plot_utility.plot_bands_by_labels(
                df=ticker_df,
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
            plot_paths.append(plot_path)

            # message_path = message_utility.write_message_by_df(
            #     ticker=ticker,
            #     name=name,
            #     df=ticker_df,
            #     future=future,
            #     peg_ratio=peg_ratio,
            #     fair_value=fair_value,
            # )
            # message_paths.append(message_path)

    print(f'Tickers too short: {too_short}')
    print(f'PEG ratio too high: {peg_ratio_too_high}')
    print(f'Weak growth: {weak_growth}')
    print(f'Not cheap: {not_cheap}')
    print(f'No fair value: {no_fair_value}')
    print(f'Total tickers: {len(tickers)}')

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(plot_paths, message_paths, application))
