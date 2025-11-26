import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import json

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)


def get_competitors_dynamic(ticker, industry, max_competitors=6):
    """
    Attempt to dynamically fetch competitors using multiple methods
    Returns empty list if unsuccessful
    """
    competitors = []

    # Method 1: Try Finviz screener
    try:
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the competitors row in Finviz
            comp_cell = soup.find('td', string='Competitors')
            if comp_cell:
                comp_links = comp_cell.find_next_sibling('td').find_all('a')
                for link in comp_links:
                    comp_ticker = link.text.strip()
                    if comp_ticker and comp_ticker != ticker:
                        competitors.append(comp_ticker)
    except Exception as e:
        print(f"Finviz scraping failed: {e}")

    # Method 2: Try Yahoo Finance related tickers
    if len(competitors) < 3:
        try:
            url = f"https://query2.finance.yahoo.com/v6/finance/recommendationsbysymbol/{ticker}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'finance' in data and 'result' in data['finance']:
                    results = data['finance']['result']
                    if results and len(results) > 0:
                        for rec in results[0].get('recommendedSymbols', [])[:max_competitors]:
                            comp_ticker = rec.get('symbol')
                            if comp_ticker and comp_ticker not in competitors:
                                competitors.append(comp_ticker)
        except Exception as e:
            print(f"Yahoo API method failed: {e}")

    # Method 3: Try to get from similar stocks API endpoint
    if len(competitors) < 3:
        try:
            # Some brokerages expose this data
            url = f"https://financialmodelingprep.com/api/v4/stock_peers?symbol={ticker}&apikey=demo"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    peers = data[0].get('peersList', [])
                    for peer in peers[:max_competitors]:
                        if peer and peer not in competitors:
                            competitors.append(peer)
        except Exception as e:
            print(f"FMP API method failed: {e}")

    # Always include the original ticker first
    if ticker not in competitors:
        competitors.insert(0, ticker)
    else:
        competitors.remove(ticker)
        competitors.insert(0, ticker)

    return competitors[:max_competitors + 1]


def analyze_stock(ticker):
    """
    Complete automated fundamental analysis - just provide ticker
    """
    stock = yf.Ticker(ticker)
    info = stock.info

    print(f"\n{'='*80}")
    print(f"FUNDAMENTAL ANALYSIS: {ticker}")
    print(f"{'='*80}\n")

    # ============================================================================
    # SECTION 1: COMPANY OVERVIEW
    # ============================================================================
    print("="*80)
    print("1. COMPANY OVERVIEW")
    print("="*80)
    print(f"Name: {info.get('longName', 'N/A')}")
    print(f"Sector: {info.get('sector', 'N/A')}")
    print(f"Industry: {info.get('industry', 'N/A')}")
    print(f"Website: {info.get('website', 'N/A')}")
    print(f"Employees: {info.get('fullTimeEmployees', 'N/A'):,}" if info.get('fullTimeEmployees') else "Employees: N/A")
    print(f"\nDescription: {info.get('longBusinessSummary', 'N/A')}")

    # ============================================================================
    # SECTION 2: CURRENT PRICE & VALUATION
    # ============================================================================
    print("\n" + "="*80)
    print("2. CURRENT PRICE & VALUATION")
    print("="*80)
    print(f"Current Price: ${info.get('currentPrice', info.get('previousClose', 'N/A'))}")
    print(f"Previous Close: ${info.get('previousClose', 'N/A')}")
    print(f"52-Week High: ${info.get('fiftyTwoWeekHigh', 'N/A')}")
    print(f"52-Week Low: ${info.get('fiftyTwoWeekLow', 'N/A')}")
    print(f"50-Day Average: ${info.get('fiftyDayAverage', 'N/A')}")
    print(f"200-Day Average: ${info.get('twoHundredDayAverage', 'N/A')}")
    print(f"\nMarket Cap: ${info.get('marketCap', 'N/A'):,}" if info.get('marketCap') else "Market Cap: N/A")
    print(f"Enterprise Value: ${info.get('enterpriseValue', 'N/A'):,}" if info.get('enterpriseValue') else "Enterprise Value: N/A")
    print(f"\nP/E Ratio (Trailing): {info.get('trailingPE', 'N/A')}")
    print(f"P/E Ratio (Forward): {info.get('forwardPE', 'N/A')}")
    print(f"PEG Ratio: {info.get('pegRatio', 'N/A')}")
    print(f"Price/Book: {info.get('priceToBook', 'N/A')}")
    print(f"Price/Sales: {info.get('priceToSalesTrailing12Months', 'N/A')}")
    print(f"EV/Revenue: {info.get('enterpriseToRevenue', 'N/A')}")
    print(f"EV/EBITDA: {info.get('enterpriseToEbitda', 'N/A')}")
    print(f"Beta: {info.get('beta', 'N/A')}")

    # ============================================================================
    # SECTION 3: PROFITABILITY & GROWTH
    # ============================================================================
    print("\n" + "="*80)
    print("3. PROFITABILITY & GROWTH")
    print("="*80)
    print(f"Profit Margin: {info.get('profitMargins', 0)*100:.2f}%" if info.get('profitMargins') else "Profit Margin: N/A")
    print(f"Operating Margin: {info.get('operatingMargins', 0)*100:.2f}%" if info.get('operatingMargins') else "Operating Margin: N/A")
    print(f"Gross Margin: {info.get('grossMargins', 0)*100:.2f}%" if info.get('grossMargins') else "Gross Margin: N/A")
    print(f"EBITDA Margin: {info.get('ebitdaMargins', 0)*100:.2f}%" if info.get('ebitdaMargins') else "EBITDA Margin: N/A")
    print(f"\nROE (Return on Equity): {info.get('returnOnEquity', 0)*100:.2f}%" if info.get('returnOnEquity') else "ROE: N/A")
    print(f"ROA (Return on Assets): {info.get('returnOnAssets', 0)*100:.2f}%" if info.get('returnOnAssets') else "ROA: N/A")
    print(f"\nRevenue Growth (YoY): {info.get('revenueGrowth', 0)*100:.2f}%" if info.get('revenueGrowth') else "Revenue Growth: N/A")
    print(f"Earnings Growth (YoY): {info.get('earningsGrowth', 0)*100:.2f}%" if info.get('earningsGrowth') else "Earnings Growth: N/A")

    # ============================================================================
    # SECTION 4: FINANCIAL HEALTH
    # ============================================================================
    print("\n" + "="*80)
    print("4. FINANCIAL HEALTH")
    print("="*80)
    print(f"Total Cash: ${info.get('totalCash', 'N/A'):,}" if info.get('totalCash') else "Total Cash: N/A")
    print(f"Total Debt: ${info.get('totalDebt', 'N/A'):,}" if info.get('totalDebt') else "Total Debt: N/A")
    print(f"Debt-to-Equity: {info.get('debtToEquity', 'N/A')}")
    print(f"Current Ratio: {info.get('currentRatio', 'N/A')}")
    print(f"Quick Ratio: {info.get('quickRatio', 'N/A')}")
    print(f"\nFree Cash Flow: ${info.get('freeCashflow', 'N/A'):,}" if info.get('freeCashflow') else "Free Cash Flow: N/A")
    print(f"Operating Cash Flow: ${info.get('operatingCashflow', 'N/A'):,}" if info.get('operatingCashflow') else "Operating Cash Flow: N/A")

    # ============================================================================
    # SECTION 5: DIVIDENDS
    # ============================================================================
    print("\n" + "="*80)
    print("5. DIVIDEND INFORMATION")
    print("="*80)
    print(f"Dividend Rate: ${info.get('dividendRate', 0)}")
    print(f"Dividend Yield: {info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "Dividend Yield: 0.00%")
    print(f"Payout Ratio: {info.get('payoutRatio', 0)*100:.2f}%" if info.get('payoutRatio') else "Payout Ratio: 0.00%")
    print(f"5-Year Avg Yield: {info.get('fiveYearAvgDividendYield', 'N/A')}")

    # ============================================================================
    # SECTION 6: OWNERSHIP & SHORT INTEREST
    # ============================================================================
    print("\n" + "="*80)
    print("6. OWNERSHIP & SHORT INTEREST")
    print("="*80)
    print(f"Insider Ownership: {info.get('heldPercentInsiders', 0)*100:.2f}%" if info.get('heldPercentInsiders') else "Insider Ownership: N/A")
    print(f"Institutional Ownership: {info.get('heldPercentInstitutions', 0)*100:.2f}%" if info.get('heldPercentInstitutions') else "Institutional Ownership: N/A")
    print(f"\nShares Outstanding: {info.get('sharesOutstanding', 'N/A'):,}" if info.get('sharesOutstanding') else "Shares Outstanding: N/A")
    print(f"Float: {info.get('floatShares', 'N/A'):,}" if info.get('floatShares') else "Float: N/A")
    print(f"Shares Short: {info.get('sharesShort', 'N/A'):,}" if info.get('sharesShort') else "Shares Short: N/A")
    print(f"Short Ratio: {info.get('shortRatio', 'N/A')}")
    print(f"Short % of Float: {info.get('shortPercentOfFloat', 0)*100:.2f}%" if info.get('shortPercentOfFloat') else "Short % of Float: N/A")

    # ============================================================================
    # SECTION 7: ANALYST TARGETS
    # ============================================================================
    print("\n" + "="*80)
    print("7. ANALYST RECOMMENDATIONS")
    print("="*80)
    print(f"Number of Analysts: {info.get('numberOfAnalystOpinions', 'N/A')}")
    print(f"Recommendation: {info.get('recommendationKey', 'N/A').upper()}" if info.get('recommendationKey') else "Recommendation: N/A")
    print(f"\nTarget High: ${info.get('targetHighPrice', 'N/A')}")
    print(f"Target Mean: ${info.get('targetMeanPrice', 'N/A')}")
    print(f"Target Median: ${info.get('targetMedianPrice', 'N/A')}")
    print(f"Target Low: ${info.get('targetLowPrice', 'N/A')}")

    current = info.get('currentPrice', info.get('previousClose', 0))
    target = info.get('targetMeanPrice', 0)
    if current and target:
        upside = ((target / current) - 1) * 100
        print(f"\nUpside to Target: {upside:+.2f}%")

    # ============================================================================
    # SECTION 8: PRICE HISTORY & VOLATILITY ANALYSIS
    # ============================================================================
    print("\n" + "="*80)
    print("8. PRICE HISTORY (Last 6 Months)")
    print("="*80)

    try:
        hist = stock.history(period="6mo")
        if not hist.empty:
            hist['Daily_Change_%'] = hist['Close'].pct_change() * 100
            hist['Volume_Ratio'] = hist['Volume'] / hist['Volume'].rolling(20).mean()

            print(f"\nTotal Trading Days: {len(hist)}")
            print(f"Period: {hist.index[0].strftime('%Y-%m-%d')} to {hist.index[-1].strftime('%Y-%m-%d')}")
            print(f"Starting Price: ${hist['Close'].iloc[0]:.2f}")
            print(f"Ending Price: ${hist['Close'].iloc[-1]:.2f}")
            print(f"6-Month Return: {((hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100):+.2f}%")
            print(f"6-Month High: ${hist['High'].max():.2f}")
            print(f"6-Month Low: ${hist['Low'].min():.2f}")
            print(f"Average Daily Volume: {hist['Volume'].mean():,.0f}")

            # Last 20 trading days
            print("\n--- Last 20 Trading Days ---")
            recent = hist[['Open', 'High', 'Low', 'Close', 'Volume', 'Daily_Change_%']].tail(20).copy()
            recent['Volume'] = recent['Volume'].apply(lambda x: f"{x:,.0f}")
            print(recent.to_string())

            # Biggest moves
            print("\n--- Top 5 Biggest Single-Day Drops ---")
            drops = hist.nsmallest(5, 'Daily_Change_%')[['Close', 'Daily_Change_%', 'Volume']].copy()
            drops['Volume'] = drops['Volume'].apply(lambda x: f"{x:,.0f}")
            print(drops.to_string())

            print("\n--- Top 5 Biggest Single-Day Gains ---")
            gains = hist.nlargest(5, 'Daily_Change_%')[['Close', 'Daily_Change_%', 'Volume']].copy()
            gains['Volume'] = gains['Volume'].apply(lambda x: f"{x:,.0f}")
            print(gains.to_string())

            # Identify unusual days (>10% move or >3x volume)
            unusual = hist[(abs(hist['Daily_Change_%']) > 10) | (hist['Volume_Ratio'] > 3)].copy()
            if not unusual.empty:
                print("\n--- UNUSUAL TRADING DAYS (>10% move or >3x volume) ---")
                unusual_display = unusual[['Open', 'Close', 'Daily_Change_%', 'Volume', 'Volume_Ratio']].copy()
                unusual_display['Volume'] = unusual_display['Volume'].apply(lambda x: f"{x:,.0f}")
                print(unusual_display.to_string())
    except Exception as e:
        print(f"Error fetching price history: {e}")

    # ============================================================================
    # SECTION 9: HISTORICAL FINANCIALS TRENDS
    # ============================================================================
    print("\n" + "="*80)
    print("9. MULTI-YEAR FINANCIAL TRENDS")
    print("="*80)

    try:
        # Revenue trend
        income_stmt = stock.income_stmt
        if income_stmt is not None and not income_stmt.empty and 'Total Revenue' in income_stmt.index:
            print("\n--- REVENUE TREND ---")
            revenue = income_stmt.loc['Total Revenue']
            for date, value in revenue.items():
                print(f"{date.year}: ${value:,.0f}")

            print("\nYear-over-Year Growth:")
            for i in range(len(revenue) - 1):
                growth = ((revenue.iloc[i] / revenue.iloc[i+1]) - 1) * 100
                print(f"  {revenue.index[i].year}: {growth:+.2f}%")

        # Net Income trend
        if income_stmt is not None and not income_stmt.empty and 'Net Income' in income_stmt.index:
            print("\n--- NET INCOME TREND ---")
            net_income = income_stmt.loc['Net Income']
            for date, value in net_income.items():
                print(f"{date.year}: ${value:,.0f}")

            print("\nYear-over-Year Growth:")
            for i in range(len(net_income) - 1):
                if net_income.iloc[i+1] != 0:
                    growth = ((net_income.iloc[i] / net_income.iloc[i+1]) - 1) * 100
                    print(f"  {net_income.index[i].year}: {growth:+.2f}%")

        # EPS trend
        if income_stmt is not None and not income_stmt.empty and 'Diluted EPS' in income_stmt.index:
            print("\n--- DILUTED EPS TREND ---")
            eps = income_stmt.loc['Diluted EPS']
            for date, value in eps.items():
                print(f"{date.year}: ${value:.2f}")

        # Free Cash Flow trend
        cashflow = stock.cashflow
        if cashflow is not None and not cashflow.empty and 'Free Cash Flow' in cashflow.index:
            print("\n--- FREE CASH FLOW TREND ---")
            fcf = cashflow.loc['Free Cash Flow']
            for date, value in fcf.items():
                if pd.notna(value):
                    print(f"{date.year}: ${value:,.0f}")

    except Exception as e:
        print(f"Error fetching financial trends: {e}")

    # ============================================================================
    # SECTION 10: QUARTERLY EARNINGS
    # ============================================================================
    print("\n" + "="*80)
    print("10. QUARTERLY EARNINGS HISTORY")
    print("="*80)

    try:
        earnings = stock.quarterly_earnings
        if earnings is not None and not earnings.empty:
            print(earnings.to_string())
    except Exception as e:
        print(f"Quarterly earnings not available: {e}")

    # ============================================================================
    # SECTION 11: INSIDER TRANSACTIONS
    # ============================================================================
    print("\n" + "="*80)
    print("11. RECENT INSIDER TRANSACTIONS (Last 15)")
    print("="*80)

    try:
        insider = stock.insider_transactions
        if insider is not None and not insider.empty:
            print(insider.head(15).to_string())
        else:
            print("No insider transaction data available")
    except Exception as e:
        print(f"Insider transactions not available: {e}")

    # ============================================================================
    # SECTION 12: INSTITUTIONAL HOLDERS
    # ============================================================================
    print("\n" + "="*80)
    print("12. TOP 10 INSTITUTIONAL HOLDERS")
    print("="*80)

    try:
        institutional = stock.institutional_holders
        if institutional is not None and not institutional.empty:
            print(institutional.head(10).to_string())
    except Exception as e:
        print(f"Institutional holders not available: {e}")

    # ============================================================================
    # SECTION 13: STOCK SPLITS & DIVIDENDS HISTORY
    # ============================================================================
    print("\n" + "="*80)
    print("13. CORPORATE ACTIONS HISTORY")
    print("="*80)

    print("\n--- STOCK SPLITS ---")
    try:
        splits = stock.splits
        if splits is not None and not splits.empty:
            for date, ratio in splits.items():
                print(f"{date.strftime('%Y-%m-%d')}: {ratio}:1 split")
        else:
            print("No stock splits in history")
    except Exception as e:
        print(f"No splits data: {e}")

    print("\n--- DIVIDEND HISTORY (Last 20) ---")
    try:
        dividends = stock.dividends
        if dividends is not None and not dividends.empty:
            for date, amount in dividends.tail(20).items():
                print(f"{date.strftime('%Y-%m-%d')}: ${amount:.4f}")
        else:
            print("No dividend payments in history")
    except Exception as e:
        print(f"No dividend data: {e}")

    # ============================================================================
    # SECTION 14: LATEST FINANCIAL STATEMENTS
    # ============================================================================
    print("\n" + "="*80)
    print("14. LATEST ANNUAL INCOME STATEMENT")
    print("="*80)

    try:
        income_stmt = stock.income_stmt
        if income_stmt is not None and not income_stmt.empty:
            print(f"\nFiscal Year: {income_stmt.columns[0]}")
            print(income_stmt.iloc[:, 0].to_string())
    except Exception as e:
        print(f"Income statement not available: {e}")

    print("\n" + "="*80)
    print("15. LATEST ANNUAL BALANCE SHEET")
    print("="*80)

    try:
        balance_sheet = stock.balance_sheet
        if balance_sheet is not None and not balance_sheet.empty:
            print(f"\nFiscal Year: {balance_sheet.columns[0]}")
            print(balance_sheet.iloc[:, 0].to_string())
    except Exception as e:
        print(f"Balance sheet not available: {e}")

    print("\n" + "="*80)
    print("16. LATEST ANNUAL CASH FLOW STATEMENT")
    print("="*80)

    try:
        cashflow = stock.cashflow
        if cashflow is not None and not cashflow.empty:
            print(f"\nFiscal Year: {cashflow.columns[0]}")
            print(cashflow.iloc[:, 0].to_string())
    except Exception as e:
        print(f"Cash flow statement not available: {e}")

    # ============================================================================
    # SECTION 17: COMPETITOR COMPARISON (DYNAMIC)
    # ============================================================================
    print("\n" + "="*80)
    print("17. COMPETITOR COMPARISON (Dynamically Fetched)")
    print("="*80)

    industry = info.get('industry', 'Unknown')
    print(f"\nAttempting to find competitors in: {industry}")
    print("This may take a moment...\n")

    competitors = get_competitors_dynamic(ticker, industry)

    if len(competitors) > 1:
        comparison_data = []
        for comp_ticker in competitors:
            try:
                comp_stock = yf.Ticker(comp_ticker)
                comp_info = comp_stock.info

                comparison_data.append({
                    'Ticker': comp_ticker,
                    'Name': comp_info.get('shortName', comp_info.get('longName', 'N/A'))[:25],
                    'Price': f"${comp_info.get('currentPrice', comp_info.get('previousClose', 0)):.2f}",
                    'Mkt Cap': f"${comp_info.get('marketCap', 0)/1e9:.1f}B" if comp_info.get('marketCap') else 'N/A',
                    'P/E': f"{comp_info.get('trailingPE', 0):.1f}" if comp_info.get('trailingPE') else 'N/A',
                    'Fwd P/E': f"{comp_info.get('forwardPE', 0):.1f}" if comp_info.get('forwardPE') else 'N/A',
                    'P/S': f"{comp_info.get('priceToSalesTrailing12Months', 0):.2f}" if comp_info.get('priceToSalesTrailing12Months') else 'N/A',
                    'Rev Gr': f"{comp_info.get('revenueGrowth', 0)*100:.1f}%" if comp_info.get('revenueGrowth') else 'N/A',
                    'Profit %': f"{comp_info.get('profitMargins', 0)*100:.1f}%" if comp_info.get('profitMargins') else 'N/A',
                    'ROE': f"{comp_info.get('returnOnEquity', 0)*100:.1f}%" if comp_info.get('returnOnEquity') else 'N/A',
                    'D/E': f"{comp_info.get('debtToEquity', 0):.1f}" if comp_info.get('debtToEquity') else 'N/A',
                })
            except Exception as e:
                print(f"Could not fetch data for {comp_ticker}: {e}")

        if comparison_data:
            df = pd.DataFrame(comparison_data)
            print(df.to_string(index=False))
        else:
            print("Could not fetch competitor data")
    else:
        print("Unable to dynamically find competitors.")
        print("Competitor comparison skipped.")

    # ============================================================================
    # END OF REPORT
    # ============================================================================
    print("\n" + "="*80)
    print("END OF FUNDAMENTAL ANALYSIS")
    print("="*80)
    print(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nℹ️  Copy this entire output and paste it back for AI analysis")
    print("="*80 + "\n")


if __name__ == '__main__':
    # Just change the ticker here
    ticker = 'NVR'

    analyze_stock(ticker)
