import asyncio
import regression_utility
import ta_utility
import telegram_service
import yfinance_service
import plot_utility


if __name__ == '__main__':
    tickers = [
        '^NDX',
        '^GDAXI',
        'BTC-EUR',
        'GME'
    ]
    future = 250

    closes = yfinance_service.get_closes(tickers, period='10y', interval='1d')

    image_paths = []

    for ticker in tickers:
        growth, lower_growth, upper_growth, lower_border, upper_border = regression_utility.get_growths(closes[ticker], future=future)
        sma_220 = ta_utility.calculate_sma_220(closes[ticker])
        rsi, rsi_sma = ta_utility.calculate_rsi(closes[ticker])
        macd, macd_signal, macd_diff = ta_utility.calculate_macd(closes[ticker])

        image_path = plot_utility.plot(
            ticker,
            closes[ticker],
            sma_220,
            [lower_border, lower_growth, growth, upper_growth, upper_border],
            start_index=len(closes[ticker]) - future,
            end_index=len(closes[ticker]),
            rsi=rsi,
            rsi_sma=rsi_sma,
            macd=macd,
            macd_signal=macd_signal,
            macd_diff=macd_diff,
        )

        image_paths.append(image_path)

    application = telegram_service.get_application()
    asyncio.run(telegram_service.send_images_to_all(image_paths, application))
