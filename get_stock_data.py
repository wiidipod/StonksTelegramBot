import datetime
import yfinance as yf

def print_today():
    today = datetime.date.today()
    print(f"Date: {today.strftime('%d-%m-%Y')}\n")

def print_yf_data(ticker):
    try:
        info = ticker.info
        symbol = info.get('symbol', 'Unknown')

        # Safely fetch metrics, defaulting to 'N/A' if missing
        name = info.get('shortName', 'N/A')
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
        fifty_two_low = info.get('fiftyTwoWeekLow', 'N/A')
        fifty_two_high = info.get('fiftyTwoWeekHigh', 'N/A')
        trailing_pe = info.get('trailingPE', 'N/A')
        forward_pe = info.get('forwardPE', 'N/A')
        revenue_growth = info.get('revenueGrowth', 'N/A')
        profit_margins = info.get('profitMargins', 'N/A')
        target_price = info.get('targetMeanPrice', 'N/A')
        recommendation = info.get('recommendationKey', 'N/A')

        # Format percentages if they exist
        if revenue_growth != 'N/A':
            revenue_growth = f"{revenue_growth * 100:.2f}%"
        if profit_margins != 'N/A':
            profit_margins = f"{profit_margins * 100:.2f}%"

        # Print the data in a clear, structured format
        print(f"--- {symbol} ({name}) ---")
        print(f"Current Price   : ${current_price}")
        print(f"52-Week Range   : ${fifty_two_low} - ${fifty_two_high}")
        print(f"Trailing P/E    : {trailing_pe}")
        print(f"Forward P/E     : {forward_pe}")
        print(f"Revenue Growth  : {revenue_growth}")
        print(f"Profit Margins  : {profit_margins}")
        print(f"Target Price    : ${target_price}")
        print(f"Analyst Rec     : {recommendation.upper()}")
        print("-" * 40)

    except Exception as e:
        print(f"--- Failed to fetch data for {ticker.ticker} ---")
        print(f"Error: {e}")
        print("-" * 40)

def main():
    symbols =[
        'ADBE',
        'AMZN',
        'CI',
        'ELV',
        'KBR',
        'LULU',
        'MSFT',
    ]
    print_today()
    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        print_yf_data(ticker)

if __name__ == "__main__":
    main()