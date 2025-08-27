import asyncio
import logging
from telegram import Update, InputMediaPhoto, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import yfinance as yf

import fundamentals_update
import message_utility
import option_utility
import ta_utility
import yfinance_service

subscribers_file = '/home/moritz/PycharmProjects/StonksTelegramBot/subscribers.txt'


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


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


async def handle_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 1:
            await update.message.reply_text("Invalid input. Try /analyze AAPL")
            return

        ticker = context.args[0]
        df = yf.download(
            [ticker],
            period='10y',
            interval='1d',
            group_by='ticker',
        )
        ticker_df = yfinance_service.extract_ticker_df(df=df, ticker=context.args[0])

        future = len(ticker_df) // 10

        dictionary, plot_path = fundamentals_update.analyze(df=ticker_df, ticker=ticker, future=future, full=True)

        message_path = message_utility.write_message_by_dictionary(dictionary=dictionary, ticker=ticker)

        await send_plot_with_message(plot_path=plot_path, message_path=message_path, chat_id=update.effective_chat.id, context=context)
    except Exception as e:
        try:
            await update.message.reply_text(f"An error occurred: {str(e)}")
        except Exception as send_error:
            logging.error(f"Failed to send error message to chat: {send_error}. Original error: {e}")

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

    await context.bot.send_message(chat_id=chat_id, text=message)


async def send_plots_to_chat_id(plot_paths, chat_id, context: ContextTypes.DEFAULT_TYPE):
    media_groups = [plot_paths[i:i + 10] for i in range(0, len(plot_paths), 10)]
    for group in media_groups:
        media = [InputMediaPhoto(open(image_path, 'rb')) for image_path in group]
        try:
            await context.bot.send_media_group(chat_id=chat_id, media=media)
        except Exception as e:
            logging.error(f"Failed to send media group to {chat_id}: {e}")
            continue


async def send_plot_with_message(plot_path, message_path, chat_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(plot_path, 'rb') as photo_file, open(message_path, 'r', encoding='utf-8') as message_file:
            caption = message_file.read()
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo_file,
                caption=caption,
                parse_mode='MarkdownV2',
            )
    except Exception as e:
        logging.error(f"Failed to send plot with message to {chat_id}: {e}")


async def send_plots_to_all(plot_paths, context: ContextTypes.DEFAULT_TYPE):
    subscribers = get_subscribers()
    media_groups = [plot_paths[i:i + 10] for i in range(0, len(plot_paths), 10)]

    for chat_id in subscribers:
        for group in media_groups:
            media = [InputMediaPhoto(open(image_path, 'rb')) for image_path in group]
            try:
                await context.bot.send_media_group(chat_id=chat_id, media=media)
            except Exception as e:
                logging.error(f"Failed to send media group to {chat_id}: {e}")
                continue


async def send_message_to_chat_id(message_path, chat_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(message_path, 'r', encoding="utf-8") as file:
            message = file.read()
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')
    except Exception as e:
        logging.error(f"Failed to send message to {chat_id}: {e}")


async def send_messages_to_all(message_paths, context: ContextTypes.DEFAULT_TYPE):
    subscribers = get_subscribers()
    messages = [open(message_path, 'r', encoding="utf-8").read() for message_path in message_paths]
    for chat_id in subscribers:
        for message in messages:
            try:
                await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')
            except Exception as e:
                logging.error(f"Failed to send message to {chat_id}: {e}")
                continue


async def send_all(plot_paths, message_paths, context: ContextTypes.DEFAULT_TYPE):
    await send_plots_to_all(plot_paths, context)
    await send_messages_to_all(message_paths, context)


async def send_plots_to_first(plot_paths, context: ContextTypes.DEFAULT_TYPE):
    chat_id = get_subscribers()[0]
    await send_plots_to_chat_id(plot_paths, chat_id, context)


async def set_commands(context: ContextTypes.DEFAULT_TYPE):
    commands = [
        BotCommand(command='start', description='Subscribe to daily updates'),
        BotCommand(command='end', description='Unsubscribe from daily updates'),
        BotCommand(command='analyze', description='/analyze AAPL'),
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

    return application


if __name__ == "__main__":
    main_application = get_application()
    asyncio.run(set_commands(main_application))
