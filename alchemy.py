import argparse
import asyncio
import traceback
import time
import yfinance as yf

from telegram_service import send_message_to_first, get_application
from ticker_service import get_all_tickers, get_nasdaq_100_tickers, chunk_list
from message_utility import human_format


def get_alchemy_scores(ticker):
    """
    Extracts the continuous variables used to score and rank the stocks.
    Handles missing yfinance data safely.
    """
    yf_ticker = yf.Ticker(ticker)
    info = yf_ticker.info
    scores = {
        'score': 1.0,
    }

    try:
        # Size: Total Enterprise Value (TEV) - Lower is better
        scores['TEV'] = info.get('enterpriseValue')
        scores['score'] /= scores['TEV']

        # Profitability: ROA - Higher is better
        scores['ROA'] = info.get('returnOnAssets')
        scores['score'] *= max(scores['ROA'], 0.0)

        # Value
        # Book-to-Market (B/M) - Higher is better
        pb_ratio = info.get('priceToBook')
        scores['B_M'] = 1 / pb_ratio if pb_ratio else None
        # Free Cash Flow Yield (FCF/P) - Higher is better
        fcf = info.get('freeCashflow')
        market_cap = info.get('marketCap')
        scores['FCF_Yield'] = (fcf / market_cap) if (fcf and market_cap) else None
        if scores['B_M'] is not None and scores['FCF_Yield'] is not None:
            scores['Value'] = (max(scores['B_M'], 0.0) * max(scores['FCF_Yield'], 0.0)) ** (1/2)
        else:
            scores['Value'] = 0.0
        scores['score'] *= scores['Value']

        # Technical
        # Contrarian Entry: Price Range - Higher is better
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        low_52 = info.get('fiftyTwoWeekLow')
        high_52 = info.get('fiftyTwoWeekHigh')

        if current_price and low_52 and high_52 and (high_52 - low_52) > 0.0:
            scores['Price_Range'] = (high_52 - current_price) / (high_52 - low_52)
        else:
            scores['Price_Range'] = None

        hist = yf_ticker.history(period="6mo")
        if not hist.empty and len(hist) > 0:
            current_close = hist['Close'].iloc[-1]

            # 3-month momentum
            three_month_index = len(hist) // 2
            if len(hist) >= three_month_index and current_close > 0:
                price_3m_ago = hist['Close'].iloc[-three_month_index]
                scores['Mom_3M'] = price_3m_ago / current_close
            else:
                scores['Mom_3M'] = None

            # 6-month momentum (first element in 6mo history)
            if current_close > 0:
                price_6m_ago = hist['Close'].iloc[0]
                scores['Mom_6M'] = price_6m_ago / current_close
            else:
                scores['Mom_6M'] = None
        else:
            scores['Mom_3M'] = None
            scores['Mom_6M'] = None
        if scores['Price_Range'] is not None and scores['Mom_3M'] is not None and scores['Mom_6M'] is not None:
            # Prevent negative numbers from turning into complex numbers
            scores['Technical'] = (max(scores['Price_Range'], 0.0) * scores['Mom_3M'] * scores['Mom_6M']) ** (1/3)
        else:
            scores['Technical'] = 0.0
        scores['score'] *= scores['Technical']

    except Exception as e:
        print(f"Error calculating scores: {e}")
        return None

    return scores


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

        # 1. Run the Hard Filter
        balance_sheet = yf_ticker.balance_sheet
        financials = yf_ticker.financials
        passes_inv_rule, rule_details = check_investment_rule(balance_sheet, financials)

        if not passes_inv_rule:
            print(f"Investment rule failed for {ticker}: {rule_details}")
            continue

        scores = get_alchemy_scores(ticker)
        if scores is None:
            continue

        ticker_scores[ticker] = scores
    return ticker_scores


def main():
    parser = argparse.ArgumentParser(description='Send plots to Telegram subscribers.')
    parser.add_argument('--all', action='store_true', help='Send plots to all subscribers')
    args = parser.parse_args()

    # tickers = get_all_tickers()
    # tickers =["AAPL", "MSFT", "PLTR", "SNOW"]
    tickers = get_nasdaq_100_tickers()
    ticker_scores = {}

    chunk_size = 100

    for i, ticker_chunk in enumerate(chunk_list(tickers, chunk_size)):
        print(f'Processing chunk {i + 1} of {len(tickers) // chunk_size + 1}')
        if i > 0:
            time.sleep(chunk_size)
        ticker_scores_chunk = process_chunk(tickers=ticker_chunk)
        ticker_scores.update(ticker_scores_chunk)

    # ---------------------------------------------------------
    # SORT AND BUILD TELEGRAM MESSAGE
    # ---------------------------------------------------------
    if not ticker_scores:
        empty_msg = "No tickers passed the investment rules."
        print(empty_msg)
        asyncio.run(send_message_to_first(message=empty_msg, context=(get_application())))
        return

    sorted_tickers = sorted(ticker_scores.items(), key=lambda item: item[1]['score'], reverse=True)
    highest_score = sorted_tickers[0][1]['score']
    lowest_score = sorted_tickers[-1][1]['score']
    score_range = highest_score - lowest_score

    top_tickers = sorted_tickers[:10]

    # Build the message line by line
    message_lines = []
    message_lines.append("🧪 *Alchemy Multibagger Screener Top 10*\n")

    # Wrap in triple backticks so Telegram uses a monospaced font (keeps columns aligned)
    message_lines.append("```text")
    message_lines.append(f"{'Ticker':<8} | {'Score':<7} | {'TEV':<7} | {'ROA':<5} | {'Value':<7} | {'Tech':<5}")
    message_lines.append("-" * 55)

    for ticker, data in top_tickers:
        raw_score = data['score']
        if score_range > 0:
            normalized_score = ((raw_score - lowest_score) / score_range) * 100
        else:
            normalized_score = 100.0

        score_str = f"{human_format(normalized_score)}%"
        tev_str = f"{human_format(data['TEV'])}" if data.get('TEV') else "N/A"
        roa_str = f"{human_format(data.get('ROA'))}" if data.get('ROA') is not None else "N/A"
        value_str = f"{human_format(data.get('Value'))}" if data.get('Value') is not None else "N/A"
        technical_str = f"{human_format(data.get('Technical'))}" if data.get('Technical') is not None else "N/A"
        message_lines.append(f"{ticker:<8} | {score_str:<7} | {tev_str:<7} | {roa_str:<5} | {value_str:<7} | {technical_str:<5}")

    # Close the code block
    message_lines.append("```")

    # Join the lines into a single string
    final_message = "\n".join(message_lines)

    # Print to console for your own logging
    print("\n" + final_message + "\n")

    # Send the final string to Telegram
    try:
        print(final_message)
        asyncio.run(send_message_to_first(
            message=final_message,
            context=(get_application())
        ))
        print("Successfully sent to Telegram.")
    except Exception as telegram_error:
        print(f"Failed to send success notification: {telegram_error}")


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
