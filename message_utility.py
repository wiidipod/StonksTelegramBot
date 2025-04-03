bearish_emoji = "📉"
bullish_emoji = "📈"
rocket_emoji = "🚀"


def write_hype_message(
        ticker,
        name,
        close,
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
    else:
        hype_emoji = bearish_emoji

    rsi_emoji = get_rsi_emoji(rsi, rsi_sma)

    macd_emoji = get_macd_emoji(macd_diff)

    message = start_message(name)
    message += f" \n **Price** ``` "
    message += f"Close: {close[-1]:16.8f} ``` "

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


def get_macd_emoji(macd_diff):
    if macd_diff[-1] > 0.0:
        macd_emoji = bullish_emoji
    else:
        macd_emoji = bearish_emoji
    return macd_emoji


def get_rsi_emoji(rsi, rsi_sma):
    if rsi[-1] < 30.0 or rsi_sma[-1] < 30.0:
        rsi_emoji = rocket_emoji
    elif rsi[-1] < 70.0 and rsi_sma[-1] < 70.0:
        rsi_emoji = bullish_emoji
    else:
        rsi_emoji = bearish_emoji
    return rsi_emoji


def write_message(
    ticker,
    name,
    close,
    sma_220,
    growths,
    future=None,
    rsi=None,
    rsi_sma=None,
    macd=None,
    macd_signal=None,
    macd_diff=None,
    peg_ratio=None,
    fair_value=None,
    one_year_estimate=None,
    upside=None,
):
    value_investing = peg_ratio is not None and fair_value is not None

    if sma_220[-1] <= close[-1]:
        sma_emoji = bullish_emoji
    else:
        sma_emoji = bearish_emoji

    if close[-1] <= growths[1][-future]:
        growth_emoji = rocket_emoji
    elif close[-1] <= growths[2][-future]:
        growth_emoji = bullish_emoji
    else:
        growth_emoji = bearish_emoji

    macd_emoji = get_macd_emoji(macd_diff)

    rsi_emoji = get_rsi_emoji(rsi, rsi_sma)

    if value_investing:
        if peg_ratio <= 1.0 and upside > 0.0:
            value_emoji = rocket_emoji
        elif peg_ratio <= 2.0 and upside > 0.0:
            value_emoji = bullish_emoji
        else:
            value_emoji = bearish_emoji
    else:
        if upside > 0.0:
            value_emoji = bullish_emoji
        else:
            value_emoji = bearish_emoji

    message = start_message(name)
    message += f" \n {sma_emoji} **Price** ``` "
    message += f"Close:   {close[-1]:16.8f} \n "
    message += f"SMA-220: {sma_220[-1]:16.8f} ``` "

    message += f" \n {growth_emoji} **Growth** ``` "
    message += f"Highest Fit: {growths[4][-future]:16.8f} \n "
    message += f"Upper Fit:   {growths[3][-future]:16.8f} \n "
    message += f"Fit:         {growths[2][-future]:16.8f} \n "
    message += f"Lower Fit:   {growths[1][-future]:16.8f} \n "
    message += f"Lowest Fit:  {growths[0][-future]:16.8f} ``` "

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
    message += f"Highest Fit:  {growths[4][-1]:16.8f} \n "
    message += f"Upper Fit:    {growths[3][-1]:16.8f} \n "
    message += f"Fit:          {growths[2][-1]:16.8f} \n "
    message += f"Lower Fit:    {growths[1][-1]:16.8f} \n "
    message += f"Lowest Fit:   {growths[0][-1]:16.8f} ``` "

    return save_message(message, ticker)


def save_message(message, ticker):
    message = message.replace('(', '\(').replace(')', '\)').replace('-', '\-')
    message_path = f"{ticker}_message.txt"
    with open(message_path, "w", encoding="utf-8") as file:
        file.write(message)
    return message_path


def start_message(name):
    message = f" **{name}** \n ".replace('.', '\.').replace('=', '\=')
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
