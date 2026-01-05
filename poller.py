import telegram_service


if __name__ == '__main__':
    application = telegram_service.get_handling_application()
    application.run_polling()
