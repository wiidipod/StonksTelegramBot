import math

import yfinance_service
from constants import DictionaryKeysNew, subscriptions_file, group_subscriptions_file
from ticker_service import sort_tickers
import telegramify_markdown


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


def _load_lines(path):
    try:
        with open(path, 'r') as file:
            return [line for line in file.read().splitlines() if line.strip()]
    except FileNotFoundError:
        return []


def _save_lines(path, lines):
    with open(path, 'w') as file:
        file.write('\n'.join(lines))


def add_entry(file_path, chat_id, item):
    """Append `chat_id$item` if absent. Return True if added, False if duplicate."""
    entries = _load_lines(file_path)
    key = f'{chat_id}${item}'
    if key in entries:
        return False
    entries.append(key)
    _save_lines(file_path, entries)
    return True


def remove_entry(file_path, chat_id, item):
    """Remove `chat_id$item` if present. Return True if removed, False if absent."""
    entries = _load_lines(file_path)
    key = f'{chat_id}${item}'
    if key not in entries:
        return False
    entries.remove(key)
    _save_lines(file_path, entries)
    return True


def wipe_entries(file_path, chat_id):
    """Drop every line starting with `chat_id$`. Return count removed."""
    entries = _load_lines(file_path)
    prefix = f'{chat_id}$'
    remaining = [e for e in entries if not e.startswith(prefix)]
    removed = len(entries) - len(remaining)
    if removed > 0:
        _save_lines(file_path, remaining)
    return removed


def list_entries(file_path, chat_id):
    """Return items for chat_id (the part after `chat_id$`)."""
    prefix = f'{chat_id}$'
    return [e[len(prefix):] for e in _load_lines(file_path) if e.startswith(prefix)]


def get_subscriptions():
    return _load_lines(subscriptions_file)


def get_group_subscriptions():
    return _load_lines(group_subscriptions_file)


def get_group_subscriptions_for_chat(chat_id):
    return sorted(set(list_entries(group_subscriptions_file, chat_id)))


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
