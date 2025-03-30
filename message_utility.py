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
):
    bearish_emoji = "\U0001F4C9"
    bullish_emoji = "\U0001F4C8"

    if sma_220[-1] <= close[-1]:
        sma_emoji = bullish_emoji
    else:
        sma_emoji = bearish_emoji

    if close[-1] <= growths[2][-future]:
        growth_emoji = bullish_emoji
    else:
        growth_emoji = bearish_emoji

    if rsi[-1] < 70 and rsi_sma[-1] < 70:
        rsi_emoji = bullish_emoji
    else:
        rsi_emoji = bearish_emoji

    if macd_diff[-1] > 0.0:
        macd_emoji = bullish_emoji
    else:
        macd_emoji = bearish_emoji

    message = f" **{name}** \n \n ".replace('.', '\.')
    message += f"{sma_emoji} **Price** ``` "
    message += f"Close:       {close[-1]:16.8f} \n "
    message += f"SMA-220:     {sma_220[-1]:16.8f} \n ``` \n "

    message += f"{growth_emoji} **Growth** ``` "
    message += f"Highest Fit: {growths[4][-future]:16.8f} \n "
    message += f"Upper Fit:   {growths[3][-future]:16.8f} \n "
    message += f"Fit:         {growths[2][-future]:16.8f} \n "
    message += f"Lower Fit:   {growths[1][-future]:16.8f} \n "
    message += f"Lowest Fit:  {growths[0][-future]:16.8f} \n ``` \n "

    message += f"{rsi_emoji} **RSI** ``` "
    message += f"RSI:         {rsi[-1]:16.8f} \n "
    message += f"RSI SMA:     {rsi_sma[-1]:16.8f} \n ``` \n "

    message += f"{macd_emoji} **MACD** ``` "
    message += f"MACD:        {macd[-1]:16.8f} \n "
    message += f"MACD Signal: {macd_signal[-1]:16.8f} \n "
    message += f"MACD Diff:   {macd_diff[-1]:16.8f} \n ``` \n "

    message += f"**Future Growth** ``` "
    message += f"Highest Fit: {growths[4][-1]:16.8f} \n "
    message += f"Upper Fit:   {growths[3][-1]:16.8f} \n "
    message += f"Fit:         {growths[2][-1]:16.8f} \n "
    message += f"Lower Fit:   {growths[1][-1]:16.8f} \n "
    message += f"Lowest Fit:  {growths[0][-1]:16.8f} ``` "

    message = message.replace('(', '\(').replace(')', '\)').replace('-', '\-')

    message_path = f"{ticker}_message.txt"

    with open(message_path, "w") as file:
        file.write(message)

    return message_path
