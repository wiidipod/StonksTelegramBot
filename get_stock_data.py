import yfinance as yf
from datetime import datetime, timedelta

def pf(k, v):  # Print if Value is present
    if v not in [None, '', 'N/A']:
        print(f"{k}: {v}")

def print_title(title):
    print(f'\n{"="*20}\n{title}\n{"="*20}')

def display_head(df, n=3):
    if df is not None and not df.empty:
        print(df.iloc[:, :n].to_string())
    else:
        print("No data available.")

def main():
    ticker = input("Enter stock ticker (e.g. MSFT): ").strip().upper()
    stock = yf.Ticker(ticker)
    info = stock.info

    print_title(f"[ {ticker} ] COMPANY PROFILE")
    for k in ['longName','symbol','exchange','sector','industry','country','website']:
        pf(k, info.get(k, 'N/A'))
    pf('Full Description', info.get('longBusinessSummary', 'N/A'))

    print_title("VALUATION & STATS")
    for k in [
        'marketCap','sharesOutstanding','currency','regularMarketPrice',
        '52WeekChange','beta','trailingPE','forwardPE','trailingEps','dividendYield', 'priceToBook'
    ]:
        pf(k, info.get(k, 'N/A'))

    print_title("KEY ANNUAL FINANCIALS (last 3 fiscal years)")
    print("Income Statement:")
    display_head(stock.financials)
    print("\nBalance Sheet:")
    display_head(stock.balance_sheet)
    print("\nCash Flow:")
    display_head(stock.cashflow)

    print_title("LATEST QUARTERLY EARNINGS CALENDAR")
    try:
        cal = stock.calendar
        print(cal.T.to_string())
    except Exception as e:
        print("No earnings calendar data.")

    print_title("LATEST ANALYST RECOMMENDATIONS")
    try:
        rec = stock.recommendations
        if rec is not None and not rec.empty:
            print(rec.tail(5).to_string())
        else:
            print("No analyst recommendation data.")
    except Exception as e:
        print("No analyst recommendation data.")

    print_title("LAST 20 DAYS: DAILY PRICE HISTORY (O/H/L/C/V)")
    try:
        end = datetime.now()
        start = end - timedelta(days=30)
        hist = stock.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'), interval='1d')
        print(hist[['Open','High','Low','Close','Volume']].tail(20).to_string())
    except Exception as e:
        print(f"Could not fetch price history: {e}")

    print('\n' + '='*10 + ' END OF DATA ' + '='*10)

    print_title("ANALYST PRICE TARGETS (1 YEAR)")
    target_keys = ['targetLowPrice', 'targetMeanPrice', 'targetMedianPrice', 'targetHighPrice']
    for k in target_keys:
        pf(k.replace('target', '1Y Target '), info.get(k, 'N/A'))
    pf('currentPrice', info.get('currentPrice', 'N/A'))

    print_title("ANALYST RECOMMENDATION SUMMARY")
    for k in [
        'recommendationMean',  # Lower is better (1=strong buy, 5=sell)
        'recommendationKey',   # "buy", "hold", etc.
        'numberOfAnalystOpinions'
    ]:
        pf(k, info.get(k, 'N/A'))

    print_title("FWD GROWTH ESTIMATES")
    for k in [
        'earningsQuarterlyGrowth',  # YOY recent EPS growth
        'revenueQuarterlyGrowth',   # YOY recent revenue growth
        'forwardEps',
        'forwardPE',
        'pegRatio'
    ]:
        pf(k, info.get(k, 'N/A'))

    print_title("PROFITABILITY")
    for k in [
        'profitMargins',  # net margin
        'operatingMargins',
        'grossMargins',
        'returnOnAssets',
        'returnOnEquity'
    ]:
        pf(k, info.get(k, 'N/A'))

    print_title("INSIDER & INSTITUTIONAL HOLDINGS")
    for k in [
        'heldPercentInsiders',
        'heldPercentInstitutions',
        'insiderOwn',
        'insiderTransPercent'
    ]:
        pf(k, info.get(k, 'N/A'))

    print_title("DEBT & LIQUIDITY")
    for k in [
        'debtToEquity',
        'currentRatio',
        'quickRatio',
        'totalCash',
        'totalDebt'
    ]:
        pf(k, info.get(k, 'N/A'))

    print_title("SIMILAR TICKERS")
    pf('relatedTickers', info.get('relatedTickers', 'N/A'))

if __name__ == "__main__":
    main()
