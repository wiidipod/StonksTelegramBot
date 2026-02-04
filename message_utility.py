import math

import yfinance_service
from constants import output_directory
from ticker_service import sort_tickers
from yfinance_service import P
from constants import DictionaryKeys


subscriptions_file = '/home/moritz/PycharmProjects/StonksTelegramBot/subscriptions.txt'

bearish_emoji = "📉"
bullish_emoji = "📈"
rocket_emoji = "🚀"
skull_emoji = "💀"

characters_to_escape = ['-', '.', '(', ')', '!', '+', '>', '<']


def escape_characters_for_markdown(text):
    for char in characters_to_escape:
        text = text.replace(char, f'\\{char}')
    return text
    # return telegram_service.escape_markdown(text)


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

    start_message = generate_start_message(name)
    message_to_escape = f" \n **Price** ``` "
    message_to_escape += f"High:  {high[-1]:16.8f} \n "
    message_to_escape += f"Close: {close[-1]:16.8f} \n "
    message_to_escape += f"Low:   {low[-1]:16.8f} ``` "

    message_to_escape += f" \n {hype_emoji} **Quarters** ``` "
    message_to_escape += f"ATH:    {constants[4]:16.8f} \n "
    message_to_escape += f"Upper:  {constants[3]:16.8f} \n "
    message_to_escape += f"Center: {constants[2]:16.8f} \n "
    message_to_escape += f"Lower:  {constants[1]:16.8f} \n "
    message_to_escape += f"Low:    {constants[0]:16.8f} ``` "

    message_to_escape = add_macd_message(
        message=message_to_escape,
        macd_emoji=macd_emoji,
        macd=macd,
        macd_signal=macd_signal,
        macd_diff=macd_diff,
    )

    message_to_escape = add_rsi_message(
        message=message_to_escape,
        rsi_emoji=rsi_emoji,
        rsi=rsi,
        rsi_sma=rsi_sma,
    )

    return save_message(start_message=start_message, message_to_escape=message_to_escape, ticker=ticker)


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
    name = yfinance_service.get_name(ticker, mono=True)
    start_message = generate_start_message(name=name)
    message_to_escape = ""
    if dictionary[DictionaryKeys.too_short]:
        message_to_escape += "   Too short \n "
    if dictionary[DictionaryKeys.peg_ratio_too_high]:
        message_to_escape += "   PEG Ratio too high \n "
    if dictionary[DictionaryKeys.price_target_too_low]:
        message_to_escape += "   Price target too low \n "
    if dictionary[DictionaryKeys.growth_too_low]:
        message_to_escape += "   Growth to volatility too low \n "
    if dictionary[DictionaryKeys.too_expensive]:
        message_to_escape += "   Not cheap \n "
    if dictionary[DictionaryKeys.no_technicals]:
        message_to_escape += "   No momentum\n "
    if dictionary[DictionaryKeys.pe_ratio_too_high]:
        message_to_escape += "   P/E Ratio too high\n "
    if dictionary[DictionaryKeys.value_too_low]:
        message_to_escape += "   Value too low\n "
    if dictionary[DictionaryKeys.ev_to_ebidta_too_high]:
        message_to_escape += "   EV/EBITDA too high\n "
    return save_message(start_message=start_message, message_to_escape=message_to_escape, ticker=ticker)


def get_message_by_dictionary(dictionary, ticker):
    name = yfinance_service.get_name(ticker, mono=True)
    start_message = generate_start_message(name=name)
    message_to_escape = ""
    if dictionary[DictionaryKeys.too_short]:
        message_to_escape += "   Too short \n "
    if dictionary[DictionaryKeys.peg_ratio_too_high]:
        message_to_escape += "   PEG Ratio too high \n "
    if dictionary[DictionaryKeys.price_target_too_low]:
        message_to_escape += "   Price target too low \n "
    if dictionary[DictionaryKeys.growth_too_low]:
        message_to_escape += "   Growth to volatility too low \n "
    if dictionary[DictionaryKeys.too_expensive]:
        message_to_escape += "   Not cheap \n "
    if dictionary[DictionaryKeys.no_technicals]:
        message_to_escape += "   No momentum\n "
    # if dictionary[DictionaryKeys.not_52w_low]:
    #     message += "   Not 52w low \n "
    # return save_message(start_message=start_message, message_to_escape=message_to_escape, ticker=ticker)
    return escape_characters_for_markdown(start_message + message_to_escape)


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

    start_message = generate_start_message(name)
    message_to_escape = f"\n {df.index[index_today].date()} ``` "
    message_to_escape += f"Open:                {df[P.O.value].iat[index_today]:16.8f} {currency} \n "
    message_to_escape += f"High:                {df[P.H.value].iat[index_today]:16.8f} {currency} \n "
    message_to_escape += f"Low:                 {df[P.L.value].iat[index_today]:16.8f} {currency} \n "
    message_to_escape += f"Close:               {df[P.C.value].iat[index_today]:16.8f} {currency} \n \n "
    message_to_escape += get_growth_message(currency, df, index_today)
    message_to_escape += "\n "
    if fair_value is None:
        message_to_escape += "``` \n "
    else:
        message_to_escape += f"Fair Value:          {fair_value:16.8f} {currency} ``` \n "
    message_to_escape += f"PEG Ratio: {peg_ratio:5.2f} \n ".replace('.', '\.')
    message_to_escape += f"\n {df.index[-1].date()} ``` "
    message_to_escape += get_growth_message(currency, df, -1)
    message_to_escape += " ``` "

    return save_message(start_message=start_message, message_to_escape=message_to_escape, ticker=ticker)


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

    start_message = generate_start_message(name)
    message_to_escape = f" \n {sma_emoji} **Price** ``` "
    message_to_escape += f"Close:   {close[-1]:16.8f}"
    if smas:
        message_to_escape += " \n "
        message_to_escape += f"SMA-200: {smas[0][-1]:16.8f} \n "
        message_to_escape += f"EMA-{window_long:3.0f}: {smas[1][-1]:16.8f} \n "
        message_to_escape += f"EMA-{window_short:3.0f}: {smas[2][-1]:16.8f} ``` "
    else:
        message_to_escape += " ``` "

    message_to_escape += f" \n {growth_emoji} **Growth** ``` "
    message_to_escape += f"Upper Fit 2: {growths[4][-future]:16.8f} \n "
    message_to_escape += f"Upper Fit:   {growths[3][-future]:16.8f} \n "
    message_to_escape += f"Fit:         {growths[2][-future]:16.8f} \n "
    message_to_escape += f"Lower Fit:   {growths[1][-future]:16.8f} \n "
    message_to_escape += f"Lower Fit 2: {growths[0][-future]:16.8f} ``` "

    # message_to_escape = add_supertrend_message(
    #     message_to_escape=message_to_escape,
    #     supertrend_emoji=supertrend_emoji,
    #     upperband=upperband,
    #     lowerband=lowerband,
    # )

    if reversal_long is not None:
        message_to_escape = add_reversal_message(
            message=message_to_escape,
            reversal_emoji=reversal_emoji,
            entry=entry,
            etf_entry=etf_entry,
        )

    message_to_escape = add_macd_message(
        message=message_to_escape,
        macd_emoji=macd_emoji,
        macd=macd,
        macd_signal=macd_signal,
        macd_diff=macd_diff,
    )

    message_to_escape = add_rsi_message(
        message=message_to_escape,
        rsi_emoji=rsi_emoji,
        rsi=rsi,
        rsi_sma=rsi_sma,
    )

    message_to_escape += f" \n {value_emoji} **Value** ``` "
    if value_investing:
        message_to_escape += f"PEG Ratio:    {peg_ratio:16.8f} \n "
        message_to_escape += f"Fair Value:   {fair_value:16.8f} \n "
    message_to_escape += f"52w Estimate: {one_year_estimate:16.8f} \n "
    message_to_escape += f"Upside:       {upside*100.0:16.8f} % \n "
    message_to_escape += f"Upper Fit 2:  {growths[4][-1]:16.8f} \n "
    message_to_escape += f"Upper Fit:    {growths[3][-1]:16.8f} \n "
    message_to_escape += f"Fit:          {growths[2][-1]:16.8f} \n "
    message_to_escape += f"Lower Fit:    {growths[1][-1]:16.8f} \n "
    message_to_escape += f"Lower Fit 2:  {growths[0][-1]:16.8f} ``` "

    return save_message(start_message=start_message, message_to_escape=message_to_escape, ticker=ticker)


def save_message(start_message, message_to_escape, ticker):
    message_to_escape = escape_characters_for_markdown(message_to_escape)
    message_path = f"{output_directory}{ticker}_message.txt"
    with open(message_path, "w", encoding="utf-8") as file:
        file.write(start_message + message_to_escape)
    return message_path


def generate_start_message(name):
    message = f" **{name}** \n "  # .replace('.', '\.').replace('=', '\=')
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
    factor = 10 ** (order - 2)
    rounded = math.floor(value / factor) * factor
    precision = max(0, -order + 2)
    return f"{sign}{rounded:.{precision}f}"


def round_up(value):
    if value == 0.0:
        return "0.0"
    sign = "-" if value < 0 else ""
    value = abs(value)
    order = math.floor(math.log10(value))
    factor = 10 ** (order - 2)
    rounded = math.ceil(value / factor) * factor
    precision = max(0, -order + 2)
    return f"{sign}{rounded:.{precision}f}"


async def get_subscriptions_message(chat_id):
    subscriptions = get_subscriptions()
    tickers = [sub.split('$')[1] for sub in subscriptions if sub.startswith(f'{chat_id}$')]
    if tickers:
        message = ""
        for ticker in sort_tickers(tickers):
            try:
                name = yfinance_service.get_name(ticker, mono=True)
            except:
                name = f"`{ticker}`"
            message += f"- {name}\n"
    else:
        message = "You have no subscriptions."
    return message


def get_subscriptions():
    try:
        with open(subscriptions_file, 'r') as file:
            subscriptions = file.read().splitlines()
    except FileNotFoundError:
        subscriptions = []
    return subscriptions


def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


def human_format_from_string(num_str):
    try:
        num = float(num_str)
    except ValueError:
        return num_str
    return human_format(num)


if __name__ == "__main__":
    # text_main = "EUZ.DE (P/E: 12.34)"
    # print(escape_characters_for_markdown(text_main))

    print(human_format_from_string("0.0"))
    print(human_format_from_string("12345"))
    print(human_format_from_string("543"))
    print(human_format_from_string("0.0098765"))
    print(human_format_from_string("-10.12345"))
    print(human_format_from_string("1.23"))
    print(human_format_from_string("0.01012345"))
    #
    # print(round_up(0.0))
    # print(round_up(12345))
    # print(round_up(543))
    # print(round_up(0.0098765))
    # print(round_up(-10.12345))
    # print(round_up(1.23))
    # print(round_up(0.01012345))
