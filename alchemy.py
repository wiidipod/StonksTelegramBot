import argparse
import asyncio
import traceback
import time
import yfinance as yf

from telegram_service import send_message_to_first, get_application
from ticker_service import get_all_tickers, get_nasdaq_100_tickers, chunk_list


def check_investment_rule(balance_sheet, financials):
    try:
        # 1. Verify we have the required rows
        if 'Total Assets' not in balance_sheet.index or 'EBITDA' not in financials.index:
            return False, "Missing 'Total Assets' or 'EBITDA' data."

        assets_data = balance_sheet.loc['Total Assets']
        ebitda_data = financials.loc['EBITDA']

        # 2. Verify we have at least 2 years of history to compare
        if len(assets_data) < 2 or len(ebitda_data) < 2:
            return False, "Not enough historical data (need at least 2 years)."

        # 3. Extract Current Year (Index 0) and Previous Year (Index 1)
        # Note: yfinance drops missing columns, so we dropna() to ensure valid numbers
        assets_data = assets_data.dropna()
        ebitda_data = ebitda_data.dropna()

        assets_current = assets_data.iloc[0]
        assets_prev = assets_data.iloc[1]

        ebitda_current = ebitda_data.iloc[0]
        ebitda_prev = ebitda_data.iloc[1]

        # 4. Handle Division by Zero
        if assets_prev == 0 or ebitda_prev == 0:
            return False, "Previous year base is zero; cannot calculate % change."

        # 5. Calculate Percentage Changes
        # Use abs() on the denominator to handle companies that had negative EBITDA last year.
        # Standard formula: (Current - Previous) / abs(Previous)
        assets_pct_change = (assets_current - assets_prev) / abs(assets_prev)
        ebitda_pct_change = (ebitda_current - ebitda_prev) / abs(ebitda_prev)

        # 6. Apply the Multibagger Rule
        passes_rule = assets_pct_change <= ebitda_pct_change

        # Format results for readability
        details = (
            f"Assets Change: {assets_pct_change:.2%} | "
            f"EBITDA Change: {ebitda_pct_change:.2%}"
        )

        return passes_rule, details

    except Exception as e:
        return False, f"Error processing data: {str(e)}"


def process_chunk(tickers):
    ticker_scores = {}
    for ticker in tickers:
        yf_ticker = yf.Ticker(ticker)
        balance_sheet = yf_ticker.balance_sheet
        financials = yf_ticker.financials
        investment_rule = check_investment_rule(balance_sheet, financials)
        # if not investment_rule:
        #     continue
        # ticker_scores[ticker] = get_score(ticker)
        ticker_scores[ticker] = [investment_rule[0], investment_rule[1]]
    return ticker_scores


def main():
    parser = argparse.ArgumentParser(description='Send plots to Telegram subscribers.')
    parser.add_argument('--all', action='store_true', help='Send plots to all subscribers')
    args = parser.parse_args()

    tickers = ["AAPL", "MSFT", "PLTR", "SNOW"]
    ticker_scores = {}

    chunk_size = 100

    for i, ticker_chunk in enumerate(chunk_list(tickers, chunk_size)):
        print(f'Processing chunk {i + 1} of {len(tickers) // chunk_size + 1}')
        if i > 0:
            time.sleep(chunk_size)
        ticker_scores_chunk = process_chunk(tickers=ticker_chunk)
        ticker_scores.update(ticker_scores_chunk)

    print(ticker_scores)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        error_message = f"Error in fundamentals_update:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(error_message)
        try:
            asyncio.run(send_message_to_first(
                message=error_message,
                context=(get_application())
            ))
        except Exception as notification_error:
            print(f"Failed to send error notification: {notification_error}")
