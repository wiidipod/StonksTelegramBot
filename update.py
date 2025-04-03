import asyncio
import regression_utility
import ta_utility
import telegram_service
import yfinance_service
import plot_utility
import message_utility


if __name__ == '__main__':
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
        'GME',
        'GC=F',
    ]
    future = 250

    closes = yfinance_service.get_closes(tickers, period='10y', interval='1d')

    upsides = {}
    all_plot_with_ta_paths = {}
    all_plot_paths = {}
    all_message_paths = {}

    for ticker in tickers:
        close = closes[ticker]

        if len(close) < 2500:
            continue

        technicals = ta_utility.get_technicals(close)
        if technicals is None:
            continue

        growth, lower_growth, upper_growth, lower_border, upper_border = regression_utility.get_growths(close, future=future)
        if growth[-future] >= growth[-1]:
            continue

        if lower_growth[-1] < close[-1]:
            continue

        rsi, rsi_sma, macd, macd_signal, macd_diff = technicals

        one_year_estimate = min(lower_border[-1], lower_growth[-future])
        upside = one_year_estimate / close[-1] - 1.0

        upsides[ticker] = upside

        sma_220 = ta_utility.get_sma(close)
        name = yfinance_service.get_name(ticker)
        growths = [lower_border, lower_growth, growth, upper_growth, upper_border]

        plot_with_ta_path = plot_utility.plot_with_ta(
            ticker,
            name,
            close,
            sma_220,
            growths,
            start_index=len(close) - future,
            end_index=len(close),
            rsi=rsi,
            rsi_sma=rsi_sma,
            macd=macd,
            macd_signal=macd_signal,
            macd_diff=macd_diff,
        )

        plot_path = plot_utility.plot(
            ticker,
            name,
            close,
            growths,
        )

        message_path = message_utility.write_message(
            ticker,
            name,
            close,
            sma_220,
            growths,
            future=future,
            rsi=rsi,
            rsi_sma=rsi_sma,
            macd=macd,
            macd_signal=macd_signal,
            macd_diff=macd_diff,
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
