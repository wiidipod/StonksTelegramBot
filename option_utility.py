import asyncio

import message_utility
import plot_utility
import regression_utility
import ta_utility
import telegram_service
import yfinance_service


def get_target(
    ticker,
    strike_price,
    option_price,
    delta,
    option_currency='EUR',
):
    underlying_price, strike_price = yfinance_service.get_price_in_currency(ticker, to_convert=strike_price, target_currency=option_currency)

    print(f'{underlying_price = }')
    print(f'{strike_price = }')

    a = (1 - delta) / (2 * strike_price - 2 * underlying_price)
    b = (delta * strike_price - underlying_price) / (strike_price - underlying_price)
    c = (underlying_price * (delta * (underlying_price - 2 * strike_price) + underlying_price)) / (2 * (strike_price - underlying_price)) + option_price

    print(a * underlying_price ** 2 + b * underlying_price + c)
    print(f'{a = }')
    print(f'{b = }')
    print(f'{c = }')

    return a * strike_price ** 2 + b * strike_price + c

    # upside = strike_price / underlying_price - 1.0
    #
    # print(f'{upside = }')
    #
    # lever = delta * underlying_price / option_price
    # return (upside * lever + 1.0) * option_price


def get_paths(ticker):
    future = 250
    close = yfinance_service.get_closes([ticker], period='10y', interval='1d')[ticker]
    rsi, rsi_sma = ta_utility.get_rsi(close)
    macd, macd_signal, macd_diff = ta_utility.get_macd(close)
    sma_200 = ta_utility.get_sma(close)
    growth, lower_growth, upper_growth, double_lower_growth, double_upper_growth = regression_utility.get_growths(close,
                                                                                                    future=future)
    name = yfinance_service.get_name(ticker)
    growths = [double_lower_growth, lower_growth, growth, upper_growth, double_upper_growth]

    one_year_estimate = growth[-1]
    upside = one_year_estimate / close[-1] - 1.0

    plot_with_ta_path = plot_utility.plot_with_ta(
        ticker,
        name,
        close,
        sma_200,
        growths,
        start_index=len(close) - future,
        end_index=len(close),
        rsi=rsi,
        rsi_sma=rsi_sma,
        macd=macd,
        macd_signal=macd_signal,
        macd_diff=macd_diff,
    )

    plot_path = plot_utility.plot_with_growths(
        ticker,
        name,
        close,
        growths,
    )

    message_path = message_utility.write_message(
        ticker,
        name,
        close,
        sma_200,
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

    return [plot_with_ta_path, plot_path,], [message_path]


def get_stop_loss(
        option_close,
        supertrend,
        delta=0.0,
        ticker='^GSPC',
        option_currency='EUR',
):
    underlying_close, supertrend = yfinance_service.get_price_in_currency(ticker, to_convert=supertrend, target_currency=option_currency)
    print(f'{underlying_close = }')
    print(f'{supertrend = }')
    if supertrend > underlying_close:
        stop_loss =  option_close * underlying_close / supertrend
    else:
        stop_loss = option_close / underlying_close * supertrend

    return stop_loss + delta


if __name__ == '__main__':
    main_ticker = '^GSPC'

    # plot_paths, message_paths = get_paths(main_ticker)
    # application = telegram_service.get_application()
    # asyncio.run(telegram_service.send_all(plot_paths, message_paths, application))

    main_stop_loss = get_stop_loss(
        option_close=2.82,
        supertrend=5331.58725504,
    )

    print(main_stop_loss)