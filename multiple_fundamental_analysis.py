import yfinance as yf


def analyze_stocks(tickers):
    results = {}

    for ticker in tickers:
        print(f"\n{'=' * 80}")
        print(f"Fetching data for {ticker}...")
        print(f"{'=' * 80}\n")

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Create a structured data dictionary
            data = {
                'ticker': ticker,
                'company_name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'country': info.get('country', 'N/A'),

                # Price Information
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', 'N/A')),
                '52w_high': info.get('fiftyTwoWeekHigh', 'N/A'),
                '52w_low': info.get('fiftyTwoWeekLow', 'N/A'),

                # Valuation Metrics
                'market_cap': info.get('marketCap', 'N/A'),
                'enterprise_value': info.get('enterpriseValue', 'N/A'),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'forward_pe': info.get('forwardPE', 'N/A'),
                'peg_ratio': info.get('pegRatio', 'N/A'),
                'price_to_book': info.get('priceToBook', 'N/A'),
                'price_to_sales': info.get('priceToSalesTrailing12Months', 'N/A'),
                'ev_to_revenue': info.get('enterpriseToRevenue', 'N/A'),
                'ev_to_ebitda': info.get('enterpriseToEbitda', 'N/A'),

                # Profitability Metrics
                'profit_margin': info.get('profitMargins', 'N/A'),
                'operating_margin': info.get('operatingMargins', 'N/A'),
                'roe': info.get('returnOnEquity', 'N/A'),
                'roa': info.get('returnOnAssets', 'N/A'),
                'roic': info.get('returnOnCapital', 'N/A'),

                # Growth Metrics
                'revenue_growth': info.get('revenueGrowth', 'N/A'),
                'earnings_growth': info.get('earningsGrowth', 'N/A'),
                'revenue_per_share': info.get('revenuePerShare', 'N/A'),
                'earnings_per_share': info.get('trailingEps', 'N/A'),

                # Financial Health
                'total_cash': info.get('totalCash', 'N/A'),
                'total_debt': info.get('totalDebt', 'N/A'),
                'debt_to_equity': info.get('debtToEquity', 'N/A'),
                'current_ratio': info.get('currentRatio', 'N/A'),
                'quick_ratio': info.get('quickRatio', 'N/A'),
                'free_cash_flow': info.get('freeCashflow', 'N/A'),
                'operating_cash_flow': info.get('operatingCashflow', 'N/A'),

                # Dividend Information
                'dividend_yield': info.get('dividendYield', 'N/A'),
                'dividend_rate': info.get('dividendRate', 'N/A'),
                'payout_ratio': info.get('payoutRatio', 'N/A'),
                'five_year_avg_dividend_yield': info.get('fiveYearAvgDividendYield', 'N/A'),

                # Analyst Estimates
                'target_mean_price': info.get('targetMeanPrice', 'N/A'),
                'target_high_price': info.get('targetHighPrice', 'N/A'),
                'target_low_price': info.get('targetLowPrice', 'N/A'),
                'recommendation': info.get('recommendationKey', 'N/A'),
                'number_of_analyst_opinions': info.get('numberOfAnalystOpinions', 'N/A'),

                # Additional Metrics
                'beta': info.get('beta', 'N/A'),
                'book_value': info.get('bookValue', 'N/A'),
                'shares_outstanding': info.get('sharesOutstanding', 'N/A'),
                'float_shares': info.get('floatShares', 'N/A'),
                'shares_short': info.get('sharesShort', 'N/A'),
                'short_ratio': info.get('shortRatio', 'N/A'),
            }

            results[ticker] = data

            # Print in a readable format
            print(f"TICKER: {data['ticker']}")
            print(f"Company: {data['company_name']}")
            print(f"Sector: {data['sector']} | Industry: {data['industry']} | Country: {data['country']}")
            print(f"\n--- PRICE INFORMATION ---")
            print(f"Current Price: ${format_number(data['current_price'])}")
            print(f"52-Week Range: ${format_number(data['52w_low'])} - ${format_number(data['52w_high'])}")

            print(f"\n--- VALUATION METRICS ---")
            print(f"Market Cap: ${format_large_number(data['market_cap'])}")
            print(f"Enterprise Value: ${format_large_number(data['enterprise_value'])}")
            print(f"P/E Ratio (TTM): {format_number(data['pe_ratio'])}")
            print(f"Forward P/E: {format_number(data['forward_pe'])}")
            print(f"PEG Ratio: {format_number(data['peg_ratio'])}")
            print(f"Price/Book: {format_number(data['price_to_book'])}")
            print(f"Price/Sales: {format_number(data['price_to_sales'])}")
            print(f"EV/Revenue: {format_number(data['ev_to_revenue'])}")
            print(f"EV/EBITDA: {format_number(data['ev_to_ebitda'])}")

            print(f"\n--- PROFITABILITY METRICS ---")
            print(f"Profit Margin: {format_percentage(data['profit_margin'])}")
            print(f"Operating Margin: {format_percentage(data['operating_margin'])}")
            print(f"ROE: {format_percentage(data['roe'])}")
            print(f"ROA: {format_percentage(data['roa'])}")
            print(f"ROIC: {format_percentage(data['roic'])}")

            print(f"\n--- GROWTH METRICS ---")
            print(f"Revenue Growth: {format_percentage(data['revenue_growth'])}")
            print(f"Earnings Growth: {format_percentage(data['earnings_growth'])}")
            print(f"Revenue Per Share: ${format_number(data['revenue_per_share'])}")
            print(f"EPS (TTM): ${format_number(data['earnings_per_share'])}")

            print(f"\n--- FINANCIAL HEALTH ---")
            print(f"Total Cash: ${format_large_number(data['total_cash'])}")
            print(f"Total Debt: ${format_large_number(data['total_debt'])}")
            print(f"Debt/Equity: {format_number(data['debt_to_equity'])}")
            print(f"Current Ratio: {format_number(data['current_ratio'])}")
            print(f"Quick Ratio: {format_number(data['quick_ratio'])}")
            print(f"Free Cash Flow: ${format_large_number(data['free_cash_flow'])}")
            print(f"Operating Cash Flow: ${format_large_number(data['operating_cash_flow'])}")

            print(f"\n--- DIVIDEND INFORMATION ---")
            print(f"Dividend Yield: {format_percentage(data['dividend_yield'])}")
            print(f"Dividend Rate: ${format_number(data['dividend_rate'])}")
            print(f"Payout Ratio: {format_percentage(data['payout_ratio'])}")
            print(f"5-Year Avg Dividend Yield: {format_percentage(data['five_year_avg_dividend_yield'])}")

            print(f"\n--- ANALYST ESTIMATES ---")
            print(f"Recommendation: {data['recommendation']}")
            print(f"Number of Analysts: {format_number(data['number_of_analyst_opinions'])}")
            print(f"Target Price - Mean: ${format_number(data['target_mean_price'])}")
            print(
                f"Target Price Range: ${format_number(data['target_low_price'])} - ${format_number(data['target_high_price'])}")

            if data['target_mean_price'] != 'N/A' and data['current_price'] != 'N/A':
                upside = ((data['target_mean_price'] - data['current_price']) / data['current_price']) * 100
                print(f"Potential Upside: {upside:.2f}%")

            print(f"\n--- ADDITIONAL METRICS ---")
            print(f"Beta: {format_number(data['beta'])}")
            print(f"Book Value Per Share: ${format_number(data['book_value'])}")
            print(f"Shares Outstanding: {format_large_number(data['shares_outstanding'])}")
            print(f"Short Ratio: {format_number(data['short_ratio'])}")

        except Exception as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
            results[ticker] = {'error': str(e)}

    print(f"\n\n{'=' * 80}")
    print("DATA COLLECTION COMPLETE")
    print(f"{'=' * 80}\n")

    return results


def format_number(value):
    """Format number for display"""
    if value == 'N/A' or value is None:
        return 'N/A'
    try:
        return f"{float(value):.2f}"
    except:
        return 'N/A'


def format_percentage(value):
    """Format percentage for display"""
    if value == 'N/A' or value is None:
        return 'N/A'
    try:
        return f"{float(value) * 100:.2f}%"
    except:
        return 'N/A'


def format_large_number(value):
    """Format large numbers (millions/billions) for display"""
    if value == 'N/A' or value is None:
        return 'N/A'
    try:
        value = float(value)
        if value >= 1e12:
            return f"{value / 1e12:.2f}T"
        elif value >= 1e9:
            return f"{value / 1e9:.2f}B"
        elif value >= 1e6:
            return f"{value / 1e6:.2f}M"
        else:
            return f"{value:,.0f}"
    except:
        return 'N/A'


if __name__ == '__main__':

    tickers_main = [
        'BLDR',
        'CDW',
        'ELV',
        'EUZ.DE',
        'FISV',
        'LULU',
        'MOH',
        'NVR',
        'CI',
        'DECK',
        'FI',
        'ODFL',
        'PGR',
    ]
    analyze_stocks(tickers_main)
