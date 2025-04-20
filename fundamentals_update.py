from time import sleep

from tqdm import tqdm

import plot_utility
import regression_utility
import ticker_service
import yfinance as yf

import yfinance_service


def chunk_list(lst, chunk_size):
    for list_index in range(0, len(lst), chunk_size):
        yield lst[list_index:list_index + chunk_size]


if __name__ == '__main__':
    # tickers = ticker_service.get_all_tickers()
    tickers = ['^GSPC']

    too_short = 0
    peg_ratio_too_high = 0
    no_growth = 0
    no_fair_value = 0

    df = yf.download(
        tickers,
        period='10y',
        interval='1d',
        group_by='ticker',
        timeout=100.0,
    )

    for ticker in tqdm(tickers):
        ticker_df = df[ticker].copy()

        # if len(ticker_df) < 2500:
        #     too_short += 1
        #     continue
        #
        # peg_ratio = yfinance_service.get_peg_ratio(ticker)
        # if peg_ratio is None or peg_ratio > 1.0:
        #     peg_ratio_too_high += 1
        #     continue

        ticker_df = regression_utility.add_growths(ticker_df, future=250)

        # print(ticker_df.tail())
        # print(ticker_df.head())

        plot_utility.plot_bands_by_labels(
            df=ticker_df,
            ticker=ticker,
            title=f'{ticker}',
            labels=[
                'Growth',
                'Growth Lower',
                'Growth Upper',
            ],
            fname=f'test_plot.png',
            yscale='log'
        )