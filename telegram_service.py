import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler


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
    media = [InputMediaPhoto(open(image_path, 'rb')) for image_path in plot_paths]
    for chat_id in subscribers:
        await context.bot.send_media_group(chat_id=chat_id, media=media)


async def send_messages_to_all(message_paths, context: ContextTypes.DEFAULT_TYPE):
    subscribers = get_subscribers()
    messages = [open(message_path, 'r').read() for message_path in message_paths]
    for chat_id in subscribers:
        for message in messages:
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')


async def send_all(plot_paths, message_paths, context: ContextTypes.DEFAULT_TYPE):
    await send_plots_to_all(plot_paths, context)
    await send_messages_to_all(message_paths, context)


def get_application():
    token = get_token()
    application = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    end_handler = CommandHandler('end', end)
    application.add_handler(end_handler)

    return application
