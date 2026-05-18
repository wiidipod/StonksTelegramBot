import asyncio
import logging

from telegram import Update, InputMediaPhoto, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import yfinance as yf

import yfinance_service
from constants import (
    group_subscriptions_file,
    subscribers_file,
    subscriptions_file,
    token_file,
)
from message_utility import (
    add_entry,
    escape_characters_for_markdown,
    get_group_subscriptions_for_chat,
    get_group_subscriptions_message,
    get_subscriptions_message,
    list_entries,
    remove_entry,
    wipe_entries,
)
import pe_utility
from ticker_service import is_stock, is_valid_group, list_group_names, get_group_counts_async


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def get_token():
    try:
        with open(token_file, 'r') as file:
            token = file.read().strip()
    except FileNotFoundError:
        logging.error("Token file not found.")
        raise
    return token


def get_subscribers():
    try:
        with open(subscribers_file, 'r') as file:
            subscribers = file.read().splitlines()
    except FileNotFoundError:
        subscribers = []
    return subscribers


def _name_or_ticker(ticker):
    try:
        return yfinance_service.get_name(ticker, mono=True)
    except Exception:
        return ticker


async def handle_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)

    if len(context.args) < 1:
        await update.message.reply_text("Invalid input. Try `/subscribe AAPL`", parse_mode='MarkdownV2')
        return

    lines = []
    for ticker in [arg.upper() for arg in context.args]:
        if ticker in list_entries(subscriptions_file, chat_id):
            lines.append(f"You are already subscribed to {_name_or_ticker(ticker)}!")
            continue
        if not await asyncio.to_thread(yfinance_service.ticker_exists, ticker):
            lines.append(f"Ticker `{ticker}` not found. Subscription rejected.")
            continue
        add_entry(subscriptions_file, chat_id, ticker)
        lines.append(f"You have been subscribed to {_name_or_ticker(ticker)}!")
    await send_message_to_chat_id(chat_id, '\n'.join(lines), context=context)


async def handle_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)

    if len(context.args) < 1:
        await update.message.reply_text("Invalid input. Try `/unsubscribe AAPL`", parse_mode='MarkdownV2')
        return

    lines = []
    for ticker in [arg.upper() for arg in context.args]:
        name = _name_or_ticker(ticker)
        if remove_entry(subscriptions_file, chat_id, ticker):
            lines.append(f"You have been unsubscribed from {name}!")
        else:
            lines.append(f"You are not subscribed to {name}!")
    await send_message_to_chat_id(chat_id, '\n'.join(lines), context=context)


async def handle_unsubscribe_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_subs = list_entries(subscriptions_file, chat_id)

    if not user_subs:
        await send_message_to_chat_id(chat_id, "You have no subscriptions to unsubscribe from!", context=context)
        return

    confirmed = len(context.args) >= 1 and context.args[0].lower() == 'confirm'
    if not confirmed:
        message = (
            f"This will remove {len(user_subs)} ticker subscription(s).\n"
            "Reply with `/unsubscribe_all confirm` to proceed."
        )
        await send_message_to_chat_id(chat_id, message, context=context)
        return

    wipe_entries(subscriptions_file, chat_id)
    await send_message_to_chat_id(chat_id, "You have been unsubscribed from all tickers!", context=context)


async def handle_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)

    message = await get_subscriptions_message(chat_id)

    await send_message_to_chat_id(chat_id, message, context=context)


async def handle_subscribe_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)

    if len(context.args) < 1:
        await update.message.reply_text(
            "Invalid input. Try `/subscribe_group euro_stoxx_50 stock_market_indices`",
            parse_mode='MarkdownV2',
        )
        return

    lines = []
    for group in [arg.lower() for arg in context.args]:
        if not is_valid_group(group):
            lines.append(f"Unknown group `{group}`. Use /groups to list available groups.")
            continue
        if add_entry(group_subscriptions_file, chat_id, group):
            lines.append(f"You have been subscribed to group `{group}`!")
        else:
            lines.append(f"You are already subscribed to group `{group}`!")
    await send_message_to_chat_id(chat_id, '\n'.join(lines), context=context)


async def handle_unsubscribe_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)

    if len(context.args) < 1:
        await update.message.reply_text(
            "Invalid input. Try `/unsubscribe_group euro_stoxx_50`",
            parse_mode='MarkdownV2',
        )
        return

    lines = []
    for group in [arg.lower() for arg in context.args]:
        if remove_entry(group_subscriptions_file, chat_id, group):
            lines.append(f"You have been unsubscribed from group `{group}`!")
        else:
            lines.append(f"You are not subscribed to group `{group}`!")
    await send_message_to_chat_id(chat_id, '\n'.join(lines), context=context)


async def handle_unsubscribe_all_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_groups = list_entries(group_subscriptions_file, chat_id)

    if not user_groups:
        await send_message_to_chat_id(chat_id, "You have no group subscriptions to unsubscribe from!", context=context)
        return

    confirmed = len(context.args) >= 1 and context.args[0].lower() == 'confirm'
    if not confirmed:
        message = (
            f"This will remove {len(user_groups)} group subscription(s).\n"
            "Reply with `/unsubscribe_all_groups confirm` to proceed."
        )
        await send_message_to_chat_id(chat_id, message, context=context)
        return

    wipe_entries(group_subscriptions_file, chat_id)
    await send_message_to_chat_id(chat_id, "You have been unsubscribed from all groups!", context=context)


async def handle_group_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    message = await get_group_subscriptions_message(chat_id)
    await send_message_to_chat_id(chat_id, message, context=context)


async def _build_groups_keyboard_for_chat(chat_id):
    subscribed = set(get_group_subscriptions_for_chat(chat_id))
    try:
        counts = await get_group_counts_async()
    except Exception as e:
        logging.error(f"Failed to fetch group counts: {e}")
        counts = {}
    rows = []
    for name in list_group_names():
        marker = "✅" if name in subscribed else "☐"
        count = counts.get(name)
        count_str = f" ({count})" if isinstance(count, int) else ""
        text = f"{marker} {name}{count_str}"
        rows.append([InlineKeyboardButton(text, callback_data=f"grp:{name}")])
    return InlineKeyboardMarkup(rows)


async def handle_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    keyboard = await _build_groups_keyboard_for_chat(chat_id)
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Tap a group to toggle subscription:",
            reply_markup=keyboard,
        )
    except Exception as e:
        logging.error(f"Failed to send groups keyboard to {chat_id}: {e}")


async def handle_group_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query is None or query.data is None:
        return
    chat_id = str(query.message.chat.id)
    data = query.data
    if not data.startswith("grp:"):
        await query.answer()
        return
    group = data[len("grp:"):]
    if not is_valid_group(group):
        await query.answer("Unknown group")
        return

    if remove_entry(group_subscriptions_file, chat_id, group):
        action = "Unsubscribed from"
    else:
        add_entry(group_subscriptions_file, chat_id, group)
        action = "Subscribed to"
    await query.answer(f"{action} {group}")

    keyboard = await _build_groups_keyboard_for_chat(chat_id)
    try:
        await query.edit_message_reply_markup(reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Failed to update groups keyboard: {e}")


async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    daily_all = chat_id in get_subscribers()
    ticker_msg = await get_subscriptions_message(chat_id)
    group_msg = await get_group_subscriptions_message(chat_id)

    daily_marker = "✅ subscribed" if daily_all else "☐ not subscribed"
    parts = [
        "**Your Status**",
        "",
        f"**Daily updates (all tickers):** {daily_marker} (use /start or /end)",
        "",
        "**Single-ticker subscriptions:**",
        ticker_msg,
        "",
        "**Group subscriptions:**",
        group_msg,
    ]
    await send_message_to_chat_id(chat_id, "\n".join(parts), context=context)


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    message = (
        "**StonksBot Commands**\n"
        "\n"
        "📊 **Analysis**\n"
        "- `/analyze TICKER` — analyze a ticker on demand\n"
        "- Send one or more tickers as plain text to analyze them\n"
        "\n"
        "🔔 **Daily updates (all tickers)**\n"
        "- `/start` — opt in to daily plots for every ticker\n"
        "- `/end` — opt out\n"
        "\n"
        "📌 **Single-ticker subscriptions**\n"
        "- `/subscribe TICKER` (alias `/sub`) — subscribe to a ticker\n"
        "- `/unsubscribe TICKER` (alias `/unsub`)\n"
        "- `/unsubscribe_all confirm` — wipe all ticker subs (requires `confirm`)\n"
        "- `/subscriptions` (alias `/subs`) — list your tickers\n"
        "\n"
        "📁 **Group subscriptions**\n"
        "- `/groups` — list all groups, marks the ones you are subscribed to\n"
        "- `/subscribe_group NAME ...` (alias `/sub_group`)\n"
        "- `/unsubscribe_group NAME ...` (alias `/unsub_group`)\n"
        "- `/unsubscribe_all_groups confirm` — wipe all group subs (requires `confirm`)\n"
        "- `/group_subscriptions` (alias `/group_subs`) — list your groups\n"
        "\n"
        "ℹ️ **Other**\n"
        "- `/status` — overview of all your subscriptions\n"
        "- `/reversal` — S&P 500 reversal pattern check\n"
        "- `/help` — show this message"
    )
    await send_message_to_chat_id(chat_id, message, context=context)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    subscribers = get_subscribers()

    if chat_id not in subscribers:
        subscribers.append(chat_id)
        with open(subscribers_file, 'w') as file:
            file.write('\n'.join(subscribers))
            message = "You have been subscribed!"
    else:
        message = "You are already subscribed!"

    await send_message_to_chat_id(chat_id, message, context=context)


async def handle_ticker_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tickers = update.message.text.strip().upper().split()
    for ticker in tickers:
        context.args = [ticker]
        await handle_analyze(update, context)


async def handle_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 1:
            await update.message.reply_text("Invalid input. Try `/analyze AAPL`", parse_mode='MarkdownV2')
            return
    except Exception as e:
        try:
            await update.message.reply_text(f"An error occurred: {str(e)}")
        except Exception as send_error:
            logging.error(f"Failed to send error message to chat: {send_error}. Original error: {e}")
        return

    for ticker in [arg.upper() for arg in context.args]:
        if is_stock(ticker):
            try:
                pe_ratios = pe_utility.get_pe_ratios()
            except Exception:
                pe_ratios = {}
        else:
            pe_ratios = {}

        try:
            from fundamentals_update_new import get_plot_path_and_message_for
            plot_path, message = get_plot_path_and_message_for(ticker, pe_ratios=pe_ratios)

            await send_plot_with_message(plot_path=plot_path, message=message, chat_id=update.effective_chat.id, context=context)
        except Exception as e:
            try:
                await update.message.reply_text(f"An error occurred: {str(e)}")
            except Exception as send_error:
                logging.error(f"Failed to send error message to chat: {send_error}. Original error: {e}")




async def handle_reversal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        gspc = yf.Ticker('^GSPC').history(period='5d', interval='1d')
        h_today = gspc['High'].iloc[-1]
        h_yesterday = gspc['High'].iloc[-2]
        l_today = gspc['Low'].iloc[-1]
        l_yesterday = gspc['Low'].iloc[-2]
        c = gspc['Close'].iloc[-1]
        o = gspc['Open'].iloc[-1]
        if h_yesterday > h_today and l_yesterday > l_today and o > c:
            us5l = yf.Ticker('US5L.DE').history(period='5d', interval='1d')
            message = f"Long\nGSPC ``` "
            message += f"Buy@high0 {h_today:16.8f} \n "
            message += f"SL@low0 {l_today:16.8f} \n "
            message += f"PA@high-1 {h_yesterday:16.8f} ``` "
            message += f"US5L ``` "
            message += f"Buy@high0 {us5l['High'].iloc[-1]:16.8f} \n "
            message += f"SL@low0 {us5l['Low'].iloc[-1]:16.8f} \n "
            message += f"PA@high-1 {us5l['High'].iloc[-2]:16.8f} ``` "
        elif h_yesterday < h_today and l_yesterday < l_today and o < c:
            us5s = yf.Ticker('US5S.DE').history(period='5d', interval='1d')
            message = f"Short\nGSPC ``` "
            message += f"Buy@high0 {l_today:16.8f} \n "
            message += f"SL@low0   {h_today:16.8f} \n "
            message += f"PA@high-1 {l_yesterday:16.8f} ``` "
            message += f"US5S ``` "
            message += f"Buy@high0 {us5s['High'].iloc[-1]:16.8f} \n "
            message += f"SL@low0   {us5s['Low'].iloc[-1]:16.8f} \n "
            message += f"PA@high-1 {us5s['High'].iloc[-2]:16.8f} ``` "
        else:
            message = "Reversal signal not met"
        await update.message.reply_text(message, parse_mode='MarkdownV2')
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    subscribers = get_subscribers()

    if chat_id in subscribers:
        subscribers.remove(chat_id)
        with open(subscribers_file, 'w') as file:
            file.write('\n'.join(subscribers))
            message = "You have been unsubscribed!"
    else:
        message = "You are not subscribed!"

    await send_message_to_chat_id(chat_id, message, context=context)


async def send_plots_to_chat_id(plot_paths, chat_id, context: ContextTypes.DEFAULT_TYPE):
    media_groups = [plot_paths[i:i + 10] for i in range(0, len(plot_paths), 10)]
    for group in media_groups:
        media = [InputMediaPhoto(open(image_path, 'rb')) for image_path in group]
        try:
            await context.bot.send_media_group(chat_id=chat_id, media=media)
        except Exception as e:
            logging.error(f"Failed to send media group to {chat_id}: {e}")
            continue


async def send_plot_with_message(plot_path, message, chat_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(plot_path, 'rb') as photo_file:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo_file,
                caption=message,
                parse_mode='MarkdownV2',
            )
    except Exception as e:
        logging.error(f"Failed to send plot with message to {chat_id}: {e}")
        logging.error(f"Plot path: {plot_path}, Message path: {message}")


async def send_plots(
    context: ContextTypes.DEFAULT_TYPE,
    plot_paths,
    messages,
    to_all=True,
    tickers=None,
    ticker_to_groups=None,
):
    if tickers is None or ticker_to_groups is None:
        if to_all:
            await send_plots_to_all(plot_paths, context, messages=messages)
        else:
            await send_plots_to_first(plot_paths, context, messages=messages)
        return

    await send_plots_grouped(
        context=context,
        plot_paths=plot_paths,
        messages=messages,
        tickers=tickers,
        ticker_to_groups=ticker_to_groups,
        to_all=to_all,
    )


async def send_plots_grouped(
    context: ContextTypes.DEFAULT_TYPE,
    plot_paths,
    messages,
    tickers,
    ticker_to_groups,
    to_all=True,
):
    if to_all:
        all_subscribers = get_subscribers()
    else:
        first = get_subscribers()
        all_subscribers = [first[0]] if first else []

    chat_to_groups = {}
    for sub in get_group_subscriptions():
        if '$' not in sub:
            continue
        cid, grp = sub.split('$', 1)
        chat_to_groups.setdefault(cid, set()).add(grp)

    for plot_path, message, ticker in zip(plot_paths, messages, tickers):
        targets = set(all_subscribers)
        ticker_groups = ticker_to_groups.get(ticker, set())
        for cid, grps in chat_to_groups.items():
            if grps & ticker_groups:
                targets.add(cid)
        for chat_id in targets:
            try:
                await send_plot_with_message(
                    plot_path=plot_path,
                    message=message,
                    chat_id=chat_id,
                    context=context,
                )
            except Exception as e:
                logging.error(f"Failed to send plot with message to {chat_id}: {e}")


async def send_plots_to_all(plot_paths, context: ContextTypes.DEFAULT_TYPE, messages=None):
    subscribers = get_subscribers()
    media_groups = [plot_paths[i:i + 10] for i in range(0, len(plot_paths), 10)]

    for chat_id in subscribers:
        if messages is None:
            for group in media_groups:
                media = [InputMediaPhoto(open(image_path, 'rb')) for image_path in group]
                try:
                    await context.bot.send_media_group(chat_id=chat_id, media=media)
                except Exception as e:
                    logging.error(f"Failed to send media group to {chat_id}: {e}")
                    continue
        else:
            for plot_path, message in zip(plot_paths, messages):
                try:
                    await send_plot_with_message(
                        plot_path=plot_path,
                        message=message,
                        chat_id=chat_id,
                        context=context,
                    )
                except Exception as e:
                    logging.error(f"Failed to send plot with message to {chat_id}: {e}")
                    continue


async def send_message_path_to_chat_id(message_path, chat_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(message_path, 'r', encoding="utf-8") as file:
            message = file.read()
            await send_message_to_chat_id(chat_id, message, context=context)
    except Exception as e:
        logging.error(f"Failed to send message to {chat_id}: {e}")


async def send_subscriptions_to_first_chat_id(context: ContextTypes.DEFAULT_TYPE):
    chat_id = get_subscribers()[0]
    message = await get_subscriptions_message(chat_id)
    await send_message_to_chat_id(chat_id, message, context)


async def send_message_to_chat_id(chat_id, message, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = escape_characters_for_markdown(message)
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')
    except Exception as e:
        logging.error(f"Failed to send message to {chat_id}: {e}")


async def send_messages_to_all(message_paths, context: ContextTypes.DEFAULT_TYPE):
    subscribers = get_subscribers()
    messages = [open(message_path, 'r', encoding="utf-8").read() for message_path in message_paths]
    for chat_id in subscribers:
        for message in messages:
            try:
                await send_message_to_chat_id(chat_id, message, context=context)
            except Exception as e:
                logging.error(f"Failed to send message to {chat_id}: {e}")
                continue


async def send_all(plot_paths, message_paths, context: ContextTypes.DEFAULT_TYPE):
    await send_plots_to_all(plot_paths, context)
    await send_messages_to_all(message_paths, context)


async def send_plots_to_first(plot_paths, context: ContextTypes.DEFAULT_TYPE, messages=None):
    chat_id = get_subscribers()[0]
    if messages is None:
        await send_plots_to_chat_id(plot_paths, chat_id, context)
    else:
        for plot_path, message in zip(plot_paths, messages):
            await send_plot_with_message(
                plot_path=plot_path,
                message=message,
                chat_id=chat_id,
                context=context
            )


async def send_message_to_first(message, context: ContextTypes.DEFAULT_TYPE):
    chat_id = get_subscribers()[0]
    await send_message_to_chat_id(chat_id, message, context)


HANDLERS = [
    # (command, aliases, description, handler_fn)
    ('start', None, 'Subscribe to daily updates', start),
    ('end', None, 'Unsubscribe from daily updates', end),
    ('analyze', None, '/analyze AAPL', handle_analyze),
    ('subscribe', ['sub'], '/subscribe AAPL', handle_subscribe),
    ('unsubscribe', ['unsub'], '/unsubscribe AAPL', handle_unsubscribe),
    ('unsubscribe_all', None, '/unsubscribe_all', handle_unsubscribe_all),
    ('subscriptions', ['subs'], 'List your subscriptions', handle_subscriptions),
    ('subscribe_group', ['sub_group'], '/subscribe_group euro_stoxx_50', handle_subscribe_group),
    ('unsubscribe_group', ['unsub_group'], '/unsubscribe_group euro_stoxx_50', handle_unsubscribe_group),
    ('unsubscribe_all_groups', None, '/unsubscribe_all_groups', handle_unsubscribe_all_groups),
    ('group_subscriptions', ['group_subs'], 'List your group subscriptions', handle_group_subscriptions),
    ('groups', None, 'List available ticker groups', handle_groups),
    ('status', None, 'Show daily, ticker, and group subscriptions', handle_status),
    ('help', None, 'Show all commands and what they do', handle_help),
]


async def set_commands(context: ContextTypes.DEFAULT_TYPE):
    commands = []
    for name, aliases, description, _ in HANDLERS:
        commands.append(BotCommand(command=name, description=description))
        for alias in aliases or []:
            commands.append(BotCommand(command=alias, description=f'/{alias} (alias for /{name})'))
    await context.bot.set_my_commands(commands)


def get_application():
    token = get_token()
    return ApplicationBuilder().token(token).build()


def get_handling_application():
    application = get_application()
    for name, aliases, _, fn in HANDLERS:
        names = [name] + list(aliases or [])
        application.add_handler(CommandHandler(names, fn))
    application.add_handler(CallbackQueryHandler(handle_group_toggle, pattern=r'^grp:'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ticker_message))
    return application


if __name__ == "__main__":
    main_application = get_application()

    name = yfinance_service.get_name('ADBE', mono=True, with_link=True)
    print(name)
    name = escape_characters_for_markdown(name)
    print(name)
    asyncio.run(
        send_message_to_first(
            message=name,
            context=main_application,
        )
    )
