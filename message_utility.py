import math

import yfinance_service
from constants import output_directory
from yfinance_service import P
from constants import DictionaryKeys


bearish_emoji = "📉"
bullish_emoji = "📈"
rocket_emoji = "🚀"
skull_emoji = "💀"

def write_hype_message(
        ticker,
        name,
        close,
        high,
        low,
        constants,
        rsi=None,
        rsi_sma=None,
        macd=None,
        macd_signal=None,
        macd_diff=None,
):
    if constants[1] > close[-1]:
        hype_emoji = rocket_emoji
    elif constants[2] > close[-1]:
        hype_emoji = bullish_emoji
    elif constants[2] > close[-1]:
        hype_emoji = bearish_emoji
    else:
        hype_emoji = skull_emoji

    rsi_emoji = get_rsi_emoji(rsi, rsi_sma)

    macd_emoji = get_macd_emoji(macd_diff)

    message = start_message(name)
    message += f" \n **Price** ``` "
    message += f"High:  {high[-1]:16.8f} \n "
    message += f"Close: {close[-1]:16.8f} \n "
    message += f"Low:   {low[-1]:16.8f} ``` "

    message += f" \n {hype_emoji} **Quarters** ``` "
    message += f"ATH:    {constants[4]:16.8f} \n "
    message += f"Upper:  {constants[3]:16.8f} \n "
    message += f"Center: {constants[2]:16.8f} \n "
    message += f"Lower:  {constants[1]:16.8f} \n "
    message += f"Low:    {constants[0]:16.8f} ``` "

    message = add_macd_message(
        message=message,
        macd_emoji=macd_emoji,
        macd=macd,
        macd_signal=macd_signal,
        macd_diff=macd_diff,
    )

    message = add_rsi_message(
        message=message,
        rsi_emoji=rsi_emoji,
        rsi=rsi,
        rsi_sma=rsi_sma,
    )

    return save_message(message, ticker)


# def get_supertrend_emoji(upperband, lowerband, close):
#     if lowerband[-1] is None:
#         return bearish_emoji
#
#     return bullish_emoji


def get_reversal_emoji(reversal_long):
    if reversal_long is None:
        return ''
    elif reversal_long:
        return rocket_emoji
    else:
        return skull_emoji


def get_macd_emoji(macd_diff):
    if macd_diff[-2] < macd_diff[-1] > 0.0:
        macd_emoji = rocket_emoji
    elif macd_diff[-1] > 0.0:
        macd_emoji = bullish_emoji
    elif macd_diff[-2] < macd_diff[-1]:
        macd_emoji = bearish_emoji
    else:
        macd_emoji = skull_emoji
    return macd_emoji


def get_rsi_emoji(rsi, rsi_sma):
    if rsi[-1] < 30.0 or rsi_sma[-1] < 30.0:
        rsi_emoji = rocket_emoji
    elif rsi[-1] > 70.0 or rsi_sma[-1] > 70.0:
        rsi_emoji = skull_emoji
    elif rsi[-1] < 50.0:
        rsi_emoji = bullish_emoji
    else:
        rsi_emoji = bearish_emoji
    return rsi_emoji


def write_message_by_dictionary(dictionary, ticker):
    name = yfinance_service.get_name(ticker)
    message = start_message(name=name)
    if dictionary[DictionaryKeys.too_short]:
        message += "   Too short \n "
    if dictionary[DictionaryKeys.peg_ratio_too_high]:
        message += "   PEG Ratio too high \n "
    if dictionary[DictionaryKeys.price_target_too_low]:
        message += "   Price target too low \n "
    if dictionary[DictionaryKeys.growth_too_low]:
        message += "   Growth to volatility too low \n "
    if dictionary[DictionaryKeys.too_expensive]:
        message += "   Not cheap \n "
    # if dictionary[DictionaryKeys.not_52w_low]:
    #     message += "   Not 52w low \n "
    return save_message(message, ticker)


def write_message_by_df(
        ticker,
        name,
        df,
        future=None,
        peg_ratio=None,
        fair_value=None,
):
    currency = yfinance_service.get_currency(ticker)
    index_today = -1 - future

    message = start_message(name)
    message += f"\n {df.index[index_today].date()} ``` "
    message += f"Open:                {df[P.O.value].iat[index_today]:16.8f} {currency} \n "
    message += f"High:                {df[P.H.value].iat[index_today]:16.8f} {currency} \n "
    message += f"Low:                 {df[P.L.value].iat[index_today]:16.8f} {currency} \n "
    message += f"Close:               {df[P.C.value].iat[index_today]:16.8f} {currency} \n \n "
    message += get_growth_message(currency, df, index_today)
    message += "\n "
    if fair_value is None:
        message += "``` \n "
    else:
        message += f"Fair Value:          {fair_value:16.8f} {currency} ``` \n "
    message += f"PEG Ratio: {peg_ratio:5.2f} \n ".replace('.', '\.')
    message += f"\n {df.index[-1].date()} ``` "
    message += get_growth_message(currency, df, -1)
    message += " ``` "

    return save_message(message, ticker)


def get_growth_message(currency, df, index):
    message = ""
    message += f"Growth Upper (High): {df['Growth Upper (High)'].iat[index]:16.8f} {currency} \n "
    message += f"Growth Upper (Low):  {df['Growth Upper (Low)'].iat[index]:16.8f} {currency} \n "
    message += f"Growth (High):       {df['Growth (High)'].iat[index]:16.8f} {currency} \n "
    message += f"Growth (Low):        {df['Growth (Low)'].iat[index]:16.8f} {currency} \n "
    message += f"Growth Lower (High): {df['Growth Lower (High)'].iat[index]:16.8f} {currency} \n "
    message += f"Growth Lower (Low):  {df['Growth Lower (Low)'].iat[index]:16.8f} {currency} \n "
    return message


def write_message(
    ticker,
    name,
    close,
    smas=None,
    window_long=None,
    window_short=None,
    growths=None,
    future=None,
    reversal_long=None,
    entry=None,
    etf_entry=None,
    rsi=None,
    rsi_sma=None,
    macd=None,
    macd_signal=None,
    macd_diff=None,
    # upperband=None,
    # lowerband=None,
    peg_ratio=None,
    fair_value=None,
    one_year_estimate=None,
    upside=None,
):
    value_investing = peg_ratio is not None and fair_value is not None

    if growths is None:
        growths = []

    if smas:
        close_above_sma_200 = smas[0][-1] <= close[-1]
        sma_short_above_sma_long = smas[1][-1] <= smas[2][-1]
        if close_above_sma_200 and sma_short_above_sma_long:
            sma_emoji = rocket_emoji
        elif close_above_sma_200 or sma_short_above_sma_long:
            sma_emoji = bullish_emoji
        elif not close_above_sma_200 and not sma_short_above_sma_long:
            sma_emoji = skull_emoji
        else:
            sma_emoji = bearish_emoji
    else:
        sma_emoji = ''

    if close[-1] < growths[1][-future]:
        growth_emoji = rocket_emoji
    elif close[-1] < growths[2][-future]:
        growth_emoji = bullish_emoji
    elif close[-1] > growths[3][-future]:
        growth_emoji = skull_emoji
    else:
        growth_emoji = bearish_emoji

    reversal_emoji = get_reversal_emoji(reversal_long)

    # supertrend_emoji = get_supertrend_emoji(upperband, lowerband, close)

    macd_emoji = get_macd_emoji(macd_diff)

    rsi_emoji = get_rsi_emoji(rsi, rsi_sma)

    if value_investing:
        if peg_ratio <= 1.0 and upside > 0.0:
            value_emoji = rocket_emoji
        elif peg_ratio <= 2.0 and upside > 0.0:
            value_emoji = bullish_emoji
        elif peg_ratio > 2.0 and upside <= 0.0:
            value_emoji = skull_emoji
        else:
            value_emoji = bearish_emoji
    else:
        if upside > 0.0:
            value_emoji = bullish_emoji
        else:
            value_emoji = bearish_emoji

    message = start_message(name)
    message += f" \n {sma_emoji} **Price** ``` "
    message += f"Close:   {close[-1]:16.8f}"
    if smas:
        message += " \n "
        message += f"SMA-200: {smas[0][-1]:16.8f} \n "
        message += f"EMA-{window_long:3.0f}: {smas[1][-1]:16.8f} \n "
        message += f"EMA-{window_short:3.0f}: {smas[2][-1]:16.8f} ``` "
    else:
        message += " ``` "

    message += f" \n {growth_emoji} **Growth** ``` "
    message += f"Upper Fit 2: {growths[4][-future]:16.8f} \n "
    message += f"Upper Fit:   {growths[3][-future]:16.8f} \n "
    message += f"Fit:         {growths[2][-future]:16.8f} \n "
    message += f"Lower Fit:   {growths[1][-future]:16.8f} \n "
    message += f"Lower Fit 2: {growths[0][-future]:16.8f} ``` "

    # message = add_supertrend_message(
    #     message=message,
    #     supertrend_emoji=supertrend_emoji,
    #     upperband=upperband,
    #     lowerband=lowerband,
    # )

    if reversal_long is not None:
        message = add_reversal_message(
            message=message,
            reversal_emoji=reversal_emoji,
            entry=entry,
            etf_entry=etf_entry,
        )

    message = add_macd_message(
        message=message,
        macd_emoji=macd_emoji,
        macd=macd,
        macd_signal=macd_signal,
        macd_diff=macd_diff,
    )

    message = add_rsi_message(
        message=message,
        rsi_emoji=rsi_emoji,
        rsi=rsi,
        rsi_sma=rsi_sma,
    )

    message += f" \n {value_emoji} **Value** ``` "
    if value_investing:
        message += f"PEG Ratio:    {peg_ratio:16.8f} \n "
        message += f"Fair Value:   {fair_value:16.8f} \n "
    message += f"52w Estimate: {one_year_estimate:16.8f} \n "
    message += f"Upside:       {upside*100.0:16.8f} % \n "
    message += f"Upper Fit 2:  {growths[4][-1]:16.8f} \n "
    message += f"Upper Fit:    {growths[3][-1]:16.8f} \n "
    message += f"Fit:          {growths[2][-1]:16.8f} \n "
    message += f"Lower Fit:    {growths[1][-1]:16.8f} \n "
    message += f"Lower Fit 2:  {growths[0][-1]:16.8f} ``` "

    return save_message(message, ticker)


def save_message(message, ticker):
    message = message.replace('(', '\(').replace(')', '\)').replace('-', '\-')
    message_path = f"{output_directory}{ticker}_message.txt"
    with open(message_path, "w", encoding="utf-8") as file:
        file.write(message)
    return message_path


def start_message(name):
    message = f" **{name}** \n ".replace('.', '\.').replace('=', '\=')
    return message


# def add_supertrend_message(message, supertrend_emoji, upperband, lowerband):
#     message += f" \n {supertrend_emoji} **Supertrend** ``` "
#     if upperband[-1] is not None:
#         message += f"Upperband: {upperband[-1]:16.8f}"
#     if lowerband[-1] is not None:
#         if upperband[-1] is not None:
#             message += " \n "
#         message += f"Lowerband: {lowerband[-1]:16.8f} ``` "
#     else:
#         message += " ``` "
#     return message


def add_reversal_message(message, reversal_emoji, entry, etf_entry=None):
    message += f" \n {reversal_emoji} **Reversal** ``` "
    message += f"Entry:      {entry:16.8f} \n "
    if etf_entry is not None:
        message += f"S&P 500 5X: {etf_entry:16.8f} ``` "
    else:
        message += " ``` "
    return message

def add_macd_message(message, macd_emoji, macd, macd_signal, macd_diff):
    message += f" \n {macd_emoji} **MACD** ``` "
    message += f"MACD:        {macd[-1]:16.8f} \n "
    message += f"MACD Signal: {macd_signal[-1]:16.8f} \n "
    message += f"MACD Diff:   {macd_diff[-1]:16.8f} ``` "
    return message


def add_rsi_message(message, rsi_emoji, rsi, rsi_sma):
    message += f" \n {rsi_emoji} **RSI** ``` "
    message += f"RSI:     {rsi[-1]:16.8f} \n "
    message += f"RSI SMA: {rsi_sma[-1]:16.8f} ``` "
    return message


def round_down(value):
    if value == 0.0:
        return "0.0"
    sign = "-" if value < 0 else ""
    value = abs(value)
    order = math.floor(math.log10(value))
    factor = 10 ** (order - 1)
    rounded = math.floor(value / factor) * factor
    precision = max(0, -order + 1)
    return f"{sign}{rounded:.{precision}f}"

def round_up(value):
    if value == 0.0:
        return "0.0"
    sign = "-" if value < 0 else ""
    value = abs(value)
    order = math.floor(math.log10(value))
    factor = 10 ** (order - 1)
    rounded = math.ceil(value / factor) * factor
    precision = max(0, -order + 1)
    return f"{sign}{rounded:.{precision}f}"


if __name__ == "__main__":
    print(round_down(0.0))
    print(round_down(12345))
    print(round_down(543))
    print(round_down(0.0098765))
    print(round_down(-10.12345))
    print(round_down(1.23))

    print(round_up(0.0))
    print(round_up(12345))
    print(round_up(543))
    print(round_up(0.0098765))
    print(round_up(-10.12345))
    print(round_up(1.23))