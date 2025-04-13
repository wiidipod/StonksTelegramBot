import asyncio
import message_utility
import plot_utility
import ta_utility
import telegram_service
import yfinance_service

if __name__ == '__main__':
    tickers = [
        'RHM.DE',
        'LDO.MI',
        'SAAB-B.ST',
        'BA.L',
        'HO.PA',
        'RR.L',
        'AIR.PA',
        'SAF.PA',
        'KOG.OL',
        'MRO.L',
        'GC=F',
    ]

    # closes = yfinance_service.get_closes(tickers, period='10y', interval='1d')
    highs, lows, closes, opens = yfinance_service.get_prices(tickers, period='10y', interval='1d')

    all_plot_with_ta_paths = []
    all_message_paths = []

    for ticker in tickers:
        close = closes[ticker]
        high = highs[ticker]
        low = lows[ticker]

        if len(close) < 2500:
            print(f'{ticker} has less than 2500 data points.')
            continue

        ath = max(close)
        if ath == close[-1]:
            print(f'{ticker} is ATH.')
            continue

        ath_index = close.index(ath)
        atl = min(close[ath_index:])
        if atl == close[-1]:
            print(f'{ticker} is LOW.')
            continue

        fourth = (ath - atl) / 4
        lower_fourth = atl + fourth
        if close[-1] > lower_fourth:
            print(f'{ticker} is above center.')
            continue

        # technicals = ta_utility.get_technicals(close)
        # if technicals is None and close[-1] > lower_fourth:
        #     print(f'{ticker} has no technicals.')
        #     continue

        # growth, lower_growth, upper_growth, lower_border, upper_border = regression_utility.get_growths(close)
        # if growth[-1] < growth[0]:
        #     print(f'{ticker} has no growth.')
        #     continue

        rsi, rsi_sma = ta_utility.get_rsi(close)
        macd, macd_signal, macd_diff = ta_utility.get_macd(close)

        low_index = close[ath_index:].index(atl) + ath_index
        center = ath - 2 * fourth
        upper_fourth = ath - fourth

        name = yfinance_service.get_name(ticker)
        constants = [atl, lower_fourth, center, upper_fourth, ath]

        plot_path = plot_utility.plot_with_constants(
            ticker,
            name,
            close[2*ath_index-low_index:],
            high[2*ath_index-low_index:],
            low[2*ath_index-low_index:],
            constants,
            rsi=rsi,
            rsi_sma=rsi_sma,
            macd=macd,
            macd_signal=macd_signal,
            macd_diff=macd_diff,
        )

        message_path = message_utility.write_hype_message(
            ticker,
            name,
            close,
            constants,
            rsi=rsi,
            rsi_sma=rsi_sma,
            macd=macd,
            macd_signal=macd_signal,
            macd_diff=macd_diff,
        )

        all_plot_with_ta_paths.append(plot_path)
        all_message_paths.append(message_path)

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(all_plot_with_ta_paths, all_message_paths, application))
