import telegram_service
import fundamentals_update
import logging
import asyncio
import pe_utility
import argparse


async def send_all(tickers, application):
    pe_ratios = pe_utility.get_pe_ratios()
    for ticker in tickers:
        plot_path, message_path = fundamentals_update.get_plot_and_message_paths_for(ticker, pe_ratios=pe_ratios)
        for chat_id in tickers[ticker]:
            try:
                await telegram_service.send_plot_with_message(
                    chat_id=chat_id,
                    plot_path=plot_path,
                    message_path=message_path,
                    context=application,
                )
            except Exception as e:
                logging.error(f'Error sending to {chat_id} for {ticker}: {e}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send plots for subscriptions.')
    parser.add_argument('--all', action='store_true', help='Send plots for every subscription to all subscribers')
    args = parser.parse_args()

    subscriptions = telegram_service.get_subscriptions()
    tickers_main = dict()
    application_main = telegram_service.get_application()

    first_chat_id = telegram_service.get_subscribers()[0]

    for subscription in subscriptions:
        chat_id_main, ticker_main = subscription.split('$')

        if not args.all and chat_id_main != first_chat_id:
            continue

        if ticker_main not in tickers_main:
            tickers_main[ticker_main] = []
        tickers_main[ticker_main].append(chat_id_main)

    asyncio.run(send_all(dict(sorted(tickers_main.items())), application_main))

# if __name__ == '__main__':
#     subscriptions = telegram_service.get_subscriptions()
#     tickers = dict()
#     application = telegram_service.get_application()
#
#     for subscription in subscriptions:
#         chat_id, ticker = subscription.split('$')
#         if ticker not in tickers:
#             tickers[ticker] = []
#         tickers[ticker].append(chat_id)
#
#     for ticker in tickers:
#         try:
#             plot_path, message_path = fundamentals_update.get_plot_and_message_paths_for(ticker)
#
#             for chat_id in tickers[ticker]:
#                 try:
#                     asyncio.run(telegram_service.send_plot_with_message(
#                         chat_id=chat_id,
#                         plot_path=plot_path,
#                         message_path=message_path,
#                         context=application,
#                     ))
#                 except Exception as e:
#                     logging.error(f'Error sending to {chat_id} for {ticker}: {e}')
#                     continue
#         except Exception as e:
#             logging.error(f'Error processing {ticker}: {e}')
#             continue
