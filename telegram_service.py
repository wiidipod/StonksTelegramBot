import asyncio
import logging
from telegram import Update, InputMediaPhoto, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

import option_utility
import ta_utility
import yfinance_service

subscribers_file = 'subscribers.txt'


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def get_token():
    try:
        with open('token', 'r') as file:
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

    await context.bot.send_message(chat_id=chat_id, text=message)


async def long(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id, user_response = await get_option_close(context, update)

    if not user_response or not user_response[-1].message.text:
        await context.bot.send_message(chat_id=chat_id, text="Timeout.")
        return

    try:
        option_close = float(user_response[-1].message.text)

        ticker = '^GSPC'
        high, low, close = yfinance_service.get_high_low_close([ticker], period='1y')
        upperband, lowerband = ta_utility.get_supertrend(high, low, close)

        stop_loss = option_utility.get_stop_loss(
            option_close=option_close,
            supertrend=lowerband[-1],
        )

        await context.bot.send_message(chat_id=chat_id, text=f"Stop Loss: {stop_loss}")
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="Invalid input.")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"An error occurred: {str(e)}")


async def short(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id, user_response = await get_option_close(context, update)

    if not user_response or not user_response[-1].message.text:
        await context.bot.send_message(chat_id=chat_id, text="Timeout.")
        return

    try:
        option_close = float(user_response[-1].message.text)

        ticker = '^GSPC'
        high, low, close = yfinance_service.get_high_low_close([ticker], period='1y')
        upperband, lowerband = ta_utility.get_supertrend(high, low, close)

        stop_loss = option_utility.get_stop_loss(
            option_close=option_close,
            supertrend=upperband[-1],
            short=True,
        )

        await context.bot.send_message(chat_id=chat_id, text=f"Stop Loss: {stop_loss}")
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="Invalid input.")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"An error occurred: {str(e)}")


async def get_option_close(context, update):
    chat_id = str(update.effective_chat.id)
    await context.bot.send_message(chat_id=chat_id, text="Option Close?")
    user_response = await context.bot.get_updates(timeout=30)
    return chat_id, user_response


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

    await context.bot.send_message(chat_id=chat_id, text=message)


async def send_plots_to_all(plot_paths, context: ContextTypes.DEFAULT_TYPE):
    subscribers = get_subscribers()
    media_groups = [plot_paths[i:i + 10] for i in range(0, len(plot_paths), 10)]

    for chat_id in subscribers:
        for group in media_groups:
            media = [InputMediaPhoto(open(image_path, 'rb')) for image_path in group]
            await context.bot.send_media_group(chat_id=chat_id, media=media)


async def send_messages_to_all(message_paths, context: ContextTypes.DEFAULT_TYPE):
    subscribers = get_subscribers()
    messages = [open(message_path, 'r', encoding="utf-8").read() for message_path in message_paths]
    for chat_id in subscribers:
        for message in messages:
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')


async def send_all(plot_paths, message_paths, context: ContextTypes.DEFAULT_TYPE):
    await send_plots_to_all(plot_paths, context)
    await send_messages_to_all(message_paths, context)


async def set_commands(context: ContextTypes.DEFAULT_TYPE):
    commands = [
        BotCommand(command='start', description='Subscribe to daily updates'),
        BotCommand(command='end', description='Unsubscribe from daily updates'),
    ]
    await context.bot.set_my_commands(commands)


def get_application():
    token = get_token()
    application = ApplicationBuilder().token(token).connection_pool_size(50).build()  # Increase pool size

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    end_handler = CommandHandler('end', end)
    application.add_handler(end_handler)

    long_handler = CommandHandler('long', long)
    application.add_handler(long_handler)

    short_handler = CommandHandler('short', short)
    application.add_handler(short_handler)

    return application


if __name__ == "__main__":
    main_application = get_application()
    asyncio.run(set_commands(main_application))
