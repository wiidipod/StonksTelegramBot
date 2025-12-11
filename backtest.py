import yfinance_service
import fundamentals_update
import message_utility
from telegram_service import send_plot_with_message, get_subscribers, get_application
import asyncio
import yfinance as yf
from datetime import date
from dateutil.relativedelta import relativedelta


async def main(ticker, end):
    print((end - relativedelta(years=10)).strftime('%Y-%m-%d'))
    print(end.strftime("%Y-%m-%d"))
    df = yf.download(
        [ticker],
        start=(end - relativedelta(years=10)).strftime('%Y-%m-%d'),
        end=end.strftime("%Y-%m-%d"),
        interval='1d',
        group_by='ticker',
    )
    ticker_df = yfinance_service.extract_ticker_df(df=df, ticker=ticker)

    future = len(ticker_df) // 10

    dictionary, plot_path = fundamentals_update.analyze(df=ticker_df, ticker=ticker, future=future, full=True)

    message_path = message_utility.write_message_by_dictionary(dictionary=dictionary, ticker=ticker)

    await send_plot_with_message(
        plot_path=plot_path,
        message=message_path,
        chat_id=get_subscribers()[0],
        context=get_application(),
    )


if __name__ == "__main__":
    ticker_main = 'NFLX'
    end_main = date(2022, 1, 31)
    asyncio.run(main(ticker_main, end_main))
