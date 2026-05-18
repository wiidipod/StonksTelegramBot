import math

import yfinance_service
from constants import DictionaryKeysNew
from ticker_service import sort_tickers
import telegramify_markdown

subscriptions_file = '/home/moritz/PycharmProjects/StonksTelegramBot/subscriptions.txt'
group_subscriptions_file = '/home/moritz/PycharmProjects/StonksTelegramBot/group_subscriptions.txt'


def escape_characters_for_markdown(text):
    return telegramify_markdown.markdownify(
        text,
        max_line_length=None,  # If you want to change the max line length for links, images, set it to the desired value.
        normalize_whitespace=False
    )


def get_message_by_dictionary_new(dictionary, ticker):
    name = yfinance_service.get_name(ticker, mono=True)
    start_message = generate_start_message(name=name)
    message_to_escape = ""
    for key in DictionaryKeysNew:
        if dictionary[key]:
            message_to_escape += f"   {key.value} \n "
    return escape_characters_for_markdown(start_message + message_to_escape)


def generate_start_message(name):
    message = f" **{name}** \n "
    return message


def round_down(value, digits=3):
    if value == 0.0:
        return "0.0"
    sign = "-" if value < 0 else ""
    value = abs(value)
    order = math.floor(math.log10(value))
    factor = 10 ** (order - (digits - 1))
    rounded = math.floor(value / factor) * factor
    precision = max(0, -order + (digits - 1))
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
            except Exception:
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


def get_group_subscriptions():
    try:
        with open(group_subscriptions_file, 'r') as file:
            lines = [line for line in file.read().splitlines() if line.strip()]
    except FileNotFoundError:
        lines = []
    return lines


def get_group_subscriptions_for_chat(chat_id):
    return sorted({
        sub.split('$', 1)[1]
        for sub in get_group_subscriptions()
        if '$' in sub and sub.split('$', 1)[0] == chat_id
    })


async def get_group_subscriptions_message(chat_id):
    groups = get_group_subscriptions_for_chat(chat_id)
    if not groups:
        return "You have no group subscriptions."
    lines = [f"- `{group}`" for group in groups]
    return "\n".join(lines)


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
    print(round_down(35.05154639175, digits=1))
    print(round_down(35.05154639175, digits=2))
    print(round_down(35.05154639175, digits=3))
    print(round_down(35.05154639175, digits=4))
    print(round_down(35.05154639175, digits=5))
