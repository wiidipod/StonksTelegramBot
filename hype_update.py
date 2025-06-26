import asyncio
import plot_utility
import telegram_service
import yfinance_service
import yfinance as yf
from yfinance_service import P

if __name__ == '__main__':
    tickers = [
        'RHM.DE',
        'R3NK.DE',
        'HAG.DE',
        'GC=F',
        'GME',
        'TSLA',
        'NVDA',
        'AAPL',
        'BTC-EUR',
        'PLTR',
        'MSTR',
        'HIMS',
        'DEZ.DE',
        'NVO',
        '1211.HK',
        'DRO.AX',
    ]

    # closes = yfinance_service.get_closes(tickers, period='10y', interval='1d')
    # highs, lows, closes, opens = yfinance_service.get_prices(tickers, period='10y', interval='1d')
    df = yf.download(
        tickers,
        period='10y',
        interval='1d',
        group_by='ticker'
    )

    plot_paths = []
    message_paths = []

    for ticker in tickers:
        ticker_df = yfinance_service.extract_ticker_df(df=df, ticker=ticker)
        # close = closes[ticker]
        # high = highs[ticker]
        # low = lows[ticker]

        # if len(ticker_df) < 2500:
        #     print(f'{ticker} has less than 2500 data points.')
        #     continue

        ath = ticker_df[P.H.value].max()
        if ath <= ticker_df[P.H.value].iat[-1]:
            print(f'{ticker} is ATH.')
            continue

        ath_index = ticker_df[P.H.value].loc[ticker_df[P.H.value] >= ath].index[0]
        ath_integer_index = ticker_df.index.get_loc(ath_index)
        low = min(ticker_df[P.L.value].loc[ath_index:])
        if low >= ticker_df[P.L.value].iat[-1]:
            print(f'{ticker} is LOW.')
            continue

        fourth = (ath - low) / 4
        lower_fourth = low + fourth
        center = ath - 2 * fourth
        upper_fourth = ath - fourth
        if lower_fourth < ticker_df[P.H.value].iat[-1] and ticker_df[P.L.value].iat[-1] < upper_fourth:
            print(f'{ticker} is central.')
            continue

        # technicals = ta_utility.get_technicals(close)
        # if technicals is None and close[-1] > lower_fourth:
        #     print(f'{ticker} has no technicals.')
        #     continue

        # growth, lower_growth, upper_growth, lower_border, upper_border = regression_utility.get_growths(close)
        # if growth[-1] < growth[0]:
        #     print(f'{ticker} has no growth.')
        #     continue

        # rsi, rsi_sma = ta_utility.get_rsi(close)
        # macd, macd_signal, macd_diff = ta_utility.get_macd(close)

        low_index = ticker_df[P.L.value].loc[ath_index:].loc[ticker_df[P.L.value].loc[ath_index:] <= low].index[0]
        low_integer_index = ticker_df.index.get_loc(low_index)
        name = yfinance_service.get_name(ticker)
        constants = [low, lower_fourth, center, upper_fourth, ath]

        try:
            index = ticker_df[P.H.value].loc[:ath_index].loc[ticker_df[P.H.value].loc[:ath_index] <= low].index[-1]
        except IndexError as e:
            print(f'Error processing {ticker}: {e}')
            continue


        plot_path = plot_utility.plot_with_constants_by_df(
            ticker,
            name,
            # close[2*ath_index-low_index:],
            # high[2*ath_index-low_index:],
            # low[2*ath_index-low_index:],
            # ticker_df.iloc[2 * ath_integer_index - low_integer_index:],
            ticker_df.loc[index:],
            constants,
            # rsi=rsi,
            # rsi_sma=rsi_sma,
            # macd=macd,
            # macd_signal=macd_signal,
            # macd_diff=macd_diff,
        )

        # message_path = message_utility.write_hype_message(
        #     ticker,
        #     name,
        #     close,
        #     high,
        #     low,
        #     constants,
        #     rsi=rsi,
        #     rsi_sma=rsi_sma,
        #     macd=macd,
        #     macd_signal=macd_signal,
        #     macd_diff=macd_diff,
        # )

        plot_paths.append(plot_path)
        # message_paths.append(message_path)

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(plot_paths, message_paths, application))
