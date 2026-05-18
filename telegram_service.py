import asyncio
import logging

import telegram
from telegram import Update, InputMediaPhoto, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import yfinance as yf

# import option_utility
import ta_utility
import yfinance_service
from message_utility import get_subscriptions
from message_utility import subscriptions_file
from message_utility import get_subscriptions_message
from message_utility import escape_characters_for_markdown
from message_utility import (
    group_subscriptions_file,
    get_group_subscriptions,
    get_group_subscriptions_for_chat,
    get_group_subscriptions_message,
)
import pe_utility
from ticker_service import is_stock, is_valid_group, list_group_names

subscribers_file = '/home/moritz/PycharmProjects/StonksTelegramBot/subscribers.txt'


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def escape_markdown(text):
    return telegram.helpers.escape_markdown(text, version=2)


def get_token():
    try:
        with open('/home/moritz/PycharmProjects/StonksTelegramBot/token', 'r') as file:
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


async def handle_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)

    if len(context.args) < 1:
        await update.message.reply_text("Invalid input. Try `/subscribe AAPL`", parse_mode='MarkdownV2')
        return

    lines = []
    for ticker in [arg.upper() for arg in context.args]:
        subscriptions = get_subscriptions()
        try:
            name = yfinance_service.get_name(ticker, mono=True)
        except:
            name = ticker
        if f'{chat_id}${ticker}' not in subscriptions:
            subscriptions.append(f'{chat_id}${ticker}')
            with open(subscriptions_file, 'w') as file:
                file.write('\n'.join(subscriptions))
            lines.append(f"You have been subscribed to {name}!")
        else:
            lines.append(f"You are already subscribed to {name}!")
    await send_message_to_chat_id(chat_id, '\n'.join(lines), context=context)


async def handle_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)

    if len(context.args) < 1:
        await update.message.reply_text("Invalid input. Try `/unsubscribe AAPL`", parse_mode='MarkdownV2')
        return

    lines = []
    for ticker in [arg.upper() for arg in context.args]:
        subscriptions = get_subscriptions()
        try:
            name = yfinance_service.get_name(ticker, mono=True)
        except:
            name = ticker
        if f'{chat_id}${ticker}' in subscriptions:
            subscriptions.remove(f'{chat_id}${ticker}')
            with open(subscriptions_file, 'w') as file:
                file.write('\n'.join(subscriptions))
            lines.append(f"You have been unsubscribed from {name}!")
        else:
            lines.append(f"You are not subscribed to {name}!")
    await send_message_to_chat_id(chat_id, '\n'.join(lines), context=context)


async def handle_unsubscribe_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    subscriptions = get_subscriptions()

    original_length = len(subscriptions)
    subscriptions = [sub for sub in subscriptions if not sub.startswith(f'{chat_id}$')]

    if len(subscriptions) < original_length:
        with open(subscriptions_file, 'w') as file:
            file.write('\n'.join(subscriptions))
            message = "You have been unsubscribed from all tickers!"
    else:
        message = "You have no subscriptions to unsubscribe from!"

    await send_message_to_chat_id(chat_id, message, context=context)


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
        existing = get_group_subscriptions()
        entry = f'{chat_id}${group}'
        if entry not in existing:
            existing.append(entry)
            with open(group_subscriptions_file, 'w') as file:
                file.write('\n'.join(existing))
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
        existing = get_group_subscriptions()
        entry = f'{chat_id}${group}'
        if entry in existing:
            existing.remove(entry)
            with open(group_subscriptions_file, 'w') as file:
                file.write('\n'.join(existing))
            lines.append(f"You have been unsubscribed from group `{group}`!")
        else:
            lines.append(f"You are not subscribed to group `{group}`!")
    await send_message_to_chat_id(chat_id, '\n'.join(lines), context=context)


async def handle_unsubscribe_all_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    existing = get_group_subscriptions()

    original_length = len(existing)
    existing = [sub for sub in existing if not sub.startswith(f'{chat_id}$')]

    if len(existing) < original_length:
        with open(group_subscriptions_file, 'w') as file:
            file.write('\n'.join(existing))
        message = "You have been unsubscribed from all groups!"
    else:
        message = "You have no group subscriptions to unsubscribe from!"

    await send_message_to_chat_id(chat_id, message, context=context)


async def handle_group_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    message = await get_group_subscriptions_message(chat_id)
    await send_message_to_chat_id(chat_id, message, context=context)


async def handle_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    names = list_group_names()
    subscribed = set(get_group_subscriptions_for_chat(chat_id))
    lines = ["Available groups:"]
    for name in names:
        marker = "✅" if name in subscribed else "☐"
        lines.append(f"{marker} `{name}`")
    message = "\n".join(lines)
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
            except:
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


# async def handle_stop_loss(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     try:
#         if len(context.args) < 1:
#             await update.message.reply_text("Invalid input. Try `/stoploss 1.23`", parse_mode='MarkdownV2')
#             return
#
#         option_close, delta, ticker = extract_option_close_delta_and_ticker(context)
#
#         high, low, close = yfinance_service.get_high_low_close(ticker, period='1y')
#         upperband, lowerband = ta_utility.get_supertrend(high, low, close)
#         if upperband[-1] is None:
#             supertrend = lowerband[-1]
#         else:
#             supertrend = upperband[-1]
#
#         stop_loss = option_utility.get_stop_loss(
#             option_close=option_close,
#             supertrend=supertrend,
#             delta=delta,
#             ticker=ticker,
#         )
#
#         await update.message.reply_text(f"Stop Loss: {stop_loss}")
#     except ValueError:
#         await update.message.reply_text("Invalid input. Please provide a valid number.")
#     except Exception as e:
#         await update.message.reply_text(f"An error occurred: {str(e)}")


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


def extract_option_close_delta_and_ticker(context):
    option_close = float(context.args[0])

    if len(context.args) > 1:
        delta = float(context.args[1])
    else:
        delta = 0.0

    if len(context.args) > 2:
        ticker = context.args[1]
    else:
        ticker = '^GSPC'
    return option_close, delta, ticker


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
        with open(plot_path, 'rb') as photo_file:  # , open(message, 'r', encoding='utf-8') as message_file:
            # caption = escape_markdown(message_file.read(), version=2)
            # caption = escape_characters_for_markdown(message_file.read())
            # caption = message_file.read()
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
        # message = escape_markdown(message, version=2)
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


async def set_commands(context: ContextTypes.DEFAULT_TYPE):
    commands = [
        BotCommand(command='start', description='Subscribe to daily updates'),
        BotCommand(command='end', description='Unsubscribe from daily updates'),
        BotCommand(command='analyze', description='/analyze AAPL'),
        BotCommand(command='subscribe', description='/subscribe AAPL'),
        BotCommand(command='sub', description='/sub AAPL (alias for /subscribe)'),
        BotCommand(command='unsubscribe', description='/unsubscribe AAPL'),
        BotCommand(command='unsub', description='/unsub AAPL (alias for /unsubscribe)'),
        BotCommand(command='unsubscribe_all', description='/unsubscribe_all'),
        BotCommand(command='subscriptions', description='List your subscriptions'),
        BotCommand(command='subs', description='List your subscriptions (alias for /subscriptions)'),
        BotCommand(command='subscribe_group', description='/subscribe_group euro_stoxx_50'),
        BotCommand(command='sub_group', description='/sub_group euro_stoxx_50 (alias for /subscribe_group)'),
        BotCommand(command='unsubscribe_group', description='/unsubscribe_group euro_stoxx_50'),
        BotCommand(command='unsub_group', description='/unsub_group euro_stoxx_50 (alias for /unsubscribe_group)'),
        BotCommand(command='unsubscribe_all_groups', description='/unsubscribe_all_groups'),
        BotCommand(command='group_subscriptions', description='List your group subscriptions'),
        BotCommand(command='group_subs', description='List your group subscriptions (alias)'),
        BotCommand(command='groups', description='List available ticker groups'),
    ]
    await context.bot.set_my_commands(commands)


def get_application():
    token = get_token()
    application = ApplicationBuilder().token(token).build()

    return application


def get_handling_application():
    application = get_application()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    end_handler = CommandHandler('end', end)
    application.add_handler(end_handler)

    analyze_handler = CommandHandler('analyze', handle_analyze)
    application.add_handler(analyze_handler)

    subscribe_handler = CommandHandler(['subscribe', 'sub'], handle_subscribe)
    application.add_handler(subscribe_handler)

    unsubscribe_handler = CommandHandler(['unsubscribe', 'unsub'], handle_unsubscribe)
    application.add_handler(unsubscribe_handler)

    unsubscribe_all_handler = CommandHandler('unsubscribe_all', handle_unsubscribe_all)
    application.add_handler(unsubscribe_all_handler)

    subscriptions_handler = CommandHandler(['subscriptions', 'subs'], handle_subscriptions)
    application.add_handler(subscriptions_handler)

    subscribe_group_handler = CommandHandler(['subscribe_group', 'sub_group'], handle_subscribe_group)
    application.add_handler(subscribe_group_handler)

    unsubscribe_group_handler = CommandHandler(['unsubscribe_group', 'unsub_group'], handle_unsubscribe_group)
    application.add_handler(unsubscribe_group_handler)

    unsubscribe_all_groups_handler = CommandHandler('unsubscribe_all_groups', handle_unsubscribe_all_groups)
    application.add_handler(unsubscribe_all_groups_handler)

    group_subscriptions_handler = CommandHandler(['group_subscriptions', 'group_subs'], handle_group_subscriptions)
    application.add_handler(group_subscriptions_handler)

    groups_handler = CommandHandler('groups', handle_groups)
    application.add_handler(groups_handler)

    ticker_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ticker_message)
    application.add_handler(ticker_handler)

    return application


if __name__ == "__main__":
    main_application = get_application()

    name = yfinance_service.get_name('ADBE', mono=True, with_link=True)
    print(name)
    name = escape_characters_for_markdown(name)
    # name = name.replace('\\', '\\\\').replace(')', '\\)')
    print(name)
    asyncio.run(
        send_message_to_first(
            message=name,
            context=main_application,
        )
    )
    # asyncio.run(set_commands(main_application))

    # asyncio.run(send_subscriptions_to_first_chat_id(context=main_application))

    # text = "EUZ.DE (P/E: 12.34)"
    # print(escape_markdown(text, version=2))
