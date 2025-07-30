import asyncio
import plot_utility
import telegram_service
import yfinance_service
import yfinance as yf
from yfinance_service import P

if __name__ == '__main__':
    tickers = [
        'RHM.DE',  # Rheinmetall AG
        'R3NK.DE',  # RENK Group AG
        'HAG.DE',  # Hensoldt AG
        'GC=F',  # Gold Futures
        'GME',  # GameStop Corp.
        'TSLA',  # Tesla, Inc.
        'NVDA',  # NVIDIA Corporation
        'AAPL',  # Apple Inc.
        'BTC-EUR',  # Bitcoin EUR Price
        'PLTR',  # Palantir Technologies Inc.
        'MSTR',  # Strategy Incorporated
        'HIMS',  # Hims & Hers Health, Inc.
        'DEZ.DE',  # DEUTZ Aktiengesellschaft
        'NVO',  # Novo Nordisk A/S
        '1211.HK',  # BYD COMPANY
        'DRO.AX',  # DroneShield Limited
        'PLTR',  # Palantir Technologies Inc.
        'ENR.DE',  # Siemens Energy AG
        '1810.HK',  # XIAOMI-W
        'QBTS',  # D-Wave Quantum Inc.
        'CLTE.NE',  # Clara Technologies Corp.
        'FLT.V',  # Volatus Aerospace Inc.
        'ASML',  # ASML Holding N.V.
        'OPEN',  # Opendoor Technologies Inc.
        '3350.T',  # Metaplanet Inc.
        'SAP.DE',  # SAP SE
        'PUM.DE',  # Puma SE
        'INTC',  # Intel Corporation
        'VOW3.DE',  # Volkswagen AG
        'MBG.DE',  # Mercedes-Benz Group AG
        'PYPL',  # PayPal Holdings, Inc.
        'HDD.F',  # Heidelberger Druckmaschinen Aktiengesellschaft
        'ADS.DE',  # Adidas AG
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

        if ticker_df[P.L.value].iat[-1] >= upper_fourth:
            print(f'{ticker} is upper fourth.')
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
