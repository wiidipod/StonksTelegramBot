import asyncio
import logging
from telegram import Update, InputMediaPhoto, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
from telegram.request import HTTPXRequest

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


async def handle_stop_loss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 1:
            await update.message.reply_text("Invalid input. Try /stoploss 1.23")
            return

        option_close, delta, ticker = extract_option_close_delta_and_ticker(context)

        high, low, close = yfinance_service.get_high_low_close(ticker, period='1y')
        upperband, lowerband = ta_utility.get_supertrend(high, low, close)
        if upperband[-1] is None:
            supertrend = lowerband[-1]
        else:
            supertrend = upperband[-1]

        stop_loss = option_utility.get_stop_loss(
            option_close=option_close,
            supertrend=supertrend,
            delta=delta,
            ticker=ticker,
        )

        await update.message.reply_text(f"Stop Loss: {stop_loss}")
    except ValueError:
        await update.message.reply_text("Invalid input. Please provide a valid number.")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")


async def handle_fivex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        high, low, close = yfinance_service.get_high_low_close('^GSPC', period='1y')
        upperband, lowerband = ta_utility.get_supertrend(high, low, close)

        if upperband[-1] is None:
            supertrend = lowerband[-1]
            message = "Long "
            ticker = 'US5L.DE'
            price = yfinance_service.get_price(ticker)
            stop_loss = ((supertrend / close[-1] - 1.0) * 5.0 + 1.0) * price
        else:
            supertrend = upperband[-1]
            message = "Short "
            ticker = 'US5S.DE'
            price = yfinance_service.get_price(ticker)
            stop_loss = price / ((supertrend / close[-1] - 1.0) * 5.0 + 1.0)

        await update.message.reply_text(f"{ticker} {message} {stop_loss:.3f}")
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
        # BotCommand(command='stoploss', description='/stoploss option_close [ticker_symbol] [option_delta]'),
        BotCommand(command='fivex', description='S&P 500 5x Daily')
    ]
    await context.bot.set_my_commands(commands)


def get_application():
    token = get_token()
    application = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    end_handler = CommandHandler('end', end)
    application.add_handler(end_handler)

    # long_handler = CommandHandler('stoploss', handle_stop_loss)
    # application.add_handler(long_handler)

    fivex_handler = CommandHandler('fivex', handle_fivex)
    application.add_handler(fivex_handler)

    return application


if __name__ == "__main__":
    main_application = get_application()
    asyncio.run(set_commands(main_application))
