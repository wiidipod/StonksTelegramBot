import asyncio
from tqdm import tqdm
import regression_utility
import ta_utility
import telegram_service
import yfinance_service
import plot_utility
import message_utility


if __name__ == '__main__':
    defaults = [
        '^GSPC',
        '^NDX',
        # 'BTC-EUR',
        'GC=F',
    ]

    tickers = [
        '^GDAXI',
        '^NDX',
        '^GSPC',
        '^DJI',
        '^MDAXI',
        '^STOXX50E',
        '^N225',
        '^TECDAX',
        '^FCHI',
        '^FTSE',
        'BTC-EUR',
        # 'GME',
        'GC=F',
    ]
    future = 250

    # closes = yfinance_service.get_closes(tickers, period='max', interval='1d')
    highs, lows, closes, opens = yfinance_service.get_prices(tickers, period='max', interval='1d')

    upsides = {}
    all_plot_with_ta_paths = {}
    all_plot_paths = {}
    all_message_paths = {}

    for ticker in tqdm(tickers):
        high = highs[ticker]
        low = lows[ticker]
        close = closes[ticker]
        open = opens[ticker]
        long, entry = ta_utility.get_reversal(high, low, close, open)
        has_signal = ticker in defaults or long is not None

        etf_entry = None
        if ticker == '^GSPC':
            if long is True:
                etf_entry, _ = yfinance_service.get_high_low('US5L.DE', period='1d', interval='1d')
            elif long is False:
                _, etf_entry = yfinance_service.get_high_low('US5S.DE', period='1d', interval='1d')

        if len(close) < 2500 and not has_signal:
            continue

        technicals = ta_utility.get_technicals(close)
        bullish, rsi, rsi_sma, macd, macd_signal, macd_diff = technicals
        # if not bullish and not has_signal:
        #     continue

        # upperband, lowerband = ta_utility.get_supertrend(high, low, close, window=14, multiplier=2)

        growth_high, lower_growth_high, upper_growth_high, double_lower_growth_high, double_upper_growth_high = regression_utility.get_growths(high, future=future)
        growth_low, lower_growth_low, upper_growth_low, double_lower_growth_low, double_upper_growth_low = regression_utility.get_growths(low, future=future)
        if growth_high[-future] >= growth_low[-1] and not has_signal:
            continue

        if lower_growth_low[-future] < high[-1] and not has_signal:
            continue

        one_year_estimate = growth_low[-1]
        upside = one_year_estimate / close[-1] - 1.0

        if one_year_estimate <= close[-1] and not has_signal:
            continue

        upsides[ticker] = upside

        window_long = 500
        window_short = 250

        sma_200 = ta_utility.get_sma(close)
        # ema_long = ta_utility.get_sma(close, window=window_long)
        # ema_short = ta_utility.get_sma(close, window=window_short)
        ema_long = ta_utility.get_ema(close, window=window_long)
        ema_short = ta_utility.get_ema(close, window=window_short)
        name = yfinance_service.get_name(ticker)

        close = close[-2500:]
        high = high[-2500:]
        low = low[-2500:]
        double_lower_growth_high = double_lower_growth_high[-2500 - future:]
        double_lower_growth_low = double_lower_growth_low[-2500 - future:]
        lower_growth_high = lower_growth_high[-2500 - future:]
        lower_growth_low = lower_growth_low[-2500 - future:]
        growth_high = growth_high[-2500 - future:]
        growth_low = growth_low[-2500 - future:]
        upper_growth_high = upper_growth_high[-2500 - future:]
        upper_growth_low = upper_growth_low[-2500 - future:]
        double_upper_growth_high = double_upper_growth_high[-2500 - future:]
        double_upper_growth_low = double_upper_growth_low[-2500 - future:]
        macd = macd[-2500:]
        macd_signal = macd_signal[-2500:]
        macd_diff = macd_diff[-2500:]
        rsi = rsi[-2500:]
        rsi_sma = rsi_sma[-2500:]
        sma_200 = sma_200[-2500:]
        ema_long = ema_long[-2500:]
        ema_short = ema_short[-2500:]
        # upperband = upperband[-2500:]
        # lowerband = lowerband[-2500:]
        growths_high = [double_lower_growth_high, lower_growth_high, growth_high, upper_growth_high, double_upper_growth_high]
        growths_low = [double_lower_growth_low, lower_growth_low, growth_low, upper_growth_low, double_upper_growth_low]
        smas = [sma_200, ema_long, ema_short]

        plot_with_ta_path = plot_utility.plot_with_ta(
            ticker,
            name,
            close,
            high,
            low,
            smas=smas,
            window_long=window_long,
            window_short=window_short,
            growths_high=growths_high,
            growths_low=growths_low,
            start_index=len(close) - future,
            end_index=len(close),
            rsi=rsi,
            rsi_sma=rsi_sma,
            macd=macd,
            macd_signal=macd_signal,
            macd_diff=macd_diff,
            # upperband=upperband,
            # lowerband=lowerband,
        )

        plot_path = plot_utility.plot_with_growths(
            ticker,
            name,
            close,
            high,
            low,
            growths_high,
            growths_low,
        )

        message_path = message_utility.write_message(
            ticker,
            name,
            close,
            smas=smas,
            window_long=window_long,
            window_short=window_short,
            growths=growths_high,
            future=future,
            reversal_long=long,
            entry=entry,
            etf_entry=etf_entry,
            rsi=rsi,
            rsi_sma=rsi_sma,
            macd=macd,
            macd_signal=macd_signal,
            macd_diff=macd_diff,
            # upperband=upperband,
            # lowerband=lowerband,
            one_year_estimate=one_year_estimate,
            upside=upside,
        )

        all_plot_with_ta_paths[ticker] = plot_with_ta_path
        all_plot_paths[ticker] = plot_path
        all_message_paths[ticker] = message_path

    plot_paths = []
    message_paths = []

    sorted_upsides = sorted(upsides.items(), key=lambda x: x[1], reverse=True)
    for ticker, upside in sorted_upsides:
        print(f"{ticker}\n    Upside: {upside:.2%}")
        plot_paths.append(all_plot_with_ta_paths[ticker])
        plot_paths.append(all_plot_paths[ticker])
        message_paths.append(all_message_paths[ticker])

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(plot_paths, message_paths, application))
