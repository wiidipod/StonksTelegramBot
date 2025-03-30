import asyncio
import regression_utility
import ta_utility
import telegram_service
import yfinance_service
import plot_utility
import message_utility


if __name__ == '__main__':
    tickers = [
        '^NDX',
        '^GDAXI',
        'BTC-EUR',
        'GME'
    ]
    future = 250

    closes = yfinance_service.get_closes(tickers, period='10y', interval='1d')

    plot_paths = []
    message_paths = []

    for ticker in tickers:
        close = closes[ticker]

        growth, lower_growth, upper_growth, lower_border, upper_border = regression_utility.get_growths(close, future=future)
        sma_220 = ta_utility.calculate_sma_220(close)
        rsi, rsi_sma = ta_utility.calculate_rsi(close)
        macd, macd_signal, macd_diff = ta_utility.calculate_macd(close)
        name = yfinance_service.get_name(ticker)

        plot_path = plot_utility.plot(
            ticker,
            name,
            close,
            sma_220,
            [lower_border, lower_growth, growth, upper_growth, upper_border],
            start_index=len(close) - future,
            end_index=len(close),
            rsi=rsi,
            rsi_sma=rsi_sma,
            macd=macd,
            macd_signal=macd_signal,
            macd_diff=macd_diff,
        )

        message_path = message_utility.write_message(
            ticker,
            name,
            close,
            sma_220,
            [lower_border, lower_growth, growth, upper_growth, upper_border],
            future=future,
            rsi=rsi,
            rsi_sma=rsi_sma,
            macd=macd,
            macd_signal=macd_signal,
            macd_diff=macd_diff,
        )

        plot_paths.append(plot_path)
        message_paths.append(message_path)

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_all(plot_paths, message_paths, application))
    # asyncio.run(telegram_service.send_plots_to_all(plot_paths, application))
    # asyncio.run(telegram_service.send_messages_to_all(message_paths, application))
