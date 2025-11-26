#!/usr/bin/env python3
"""
Test script to verify cryptocurrency regression support
"""
import yfinance as yf
import yfinance_service
import regression_utility
import plot_utility
from ticker_service import is_crypto
import pandas as pd
import os

def test_crypto_regression():
    # Test with a cryptocurrency
    crypto_ticker = 'BTC-USD'
    print(f"\nTesting with cryptocurrency: {crypto_ticker}")
    print(f"is_crypto({crypto_ticker}) = {is_crypto(crypto_ticker)}")

    # Download crypto data
    crypto_df = yf.download(
        [crypto_ticker],
        period='10y',
        interval='1d',
        group_by='ticker',
    )
    crypto_df = yfinance_service.extract_ticker_df(df=crypto_df, ticker=crypto_ticker)

    if len(crypto_df) > 0:
        print(f"Downloaded {len(crypto_df)} days of data")

        # Apply regression with is_crypto=True
        # Match fundamentals_update.py: window = len(df)-1, future = len(df)//10
        window = len(crypto_df) - 1
        future = len(crypto_df) // 10  # 1/10th of 10 years = ~1 year forecast
        crypto_df = regression_utility.add_close_window_growths(
            crypto_df,
            window=window,
            future=future,
            is_crypto=True
        )

        print(f"\nCryptocurrency regression results:")
        print(f"Growth columns: {[col for col in crypto_df.columns if 'Growth' in col]}")
        print(f"Last actual close: {crypto_df['Close'].dropna().iloc[-1]:.2f}")
        print(f"Last growth value: {crypto_df['Growth'].dropna().iloc[-1]:.2f}")
        print(f"Growth lower: {crypto_df['Growth Lower'].dropna().iloc[-1]:.2f}")
        print(f"Growth upper: {crypto_df['Growth Upper'].dropna().iloc[-1]:.2f}")

        # Check if future dates include weekends (they should for crypto)
        future_dates = crypto_df.index[-future:]
        last_actual_date = crypto_df['Close'].dropna().index[-1]
        final_prediction_date = crypto_df['Growth'].dropna().index[-1]

        print(f"\nDate information:")
        print(f"Last actual data date: {last_actual_date.strftime('%Y-%m-%d (%A)')}")
        print(f"Final prediction date: {final_prediction_date.strftime('%Y-%m-%d (%A)')}")
        print(f"Days into future: {(final_prediction_date - last_actual_date).days}")
        print(f"\nFuture dates (last 5): {list(future_dates[-5:])}")
        print(f"Includes weekends: {any(d.weekday() >= 5 for d in future_dates)}")

        # Generate visual plot
        plot_path = plot_utility.plot_bands_by_labels(
            df=crypto_df,
            ticker=crypto_ticker,
            title=f"{crypto_ticker} - LINEAR REGRESSION (Cryptocurrency)",
            subtitle=f"Linear regression",
            labels=[
                'Growth Upper',
                'Growth',
                'Growth Lower',
            ],
            yscale='linear',
            today=-1-future,
            close_only=True,
        )
        print(f"\n📊 Crypto plot saved to: {plot_path}")

        return plot_path
    else:
        print("No data downloaded for cryptocurrency")
        return None


def test_stock_regression():
    # Test with a regular stock
    stock_ticker = 'AAPL'
    print(f"\n\nTesting with stock: {stock_ticker}")
    print(f"is_crypto({stock_ticker}) = {is_crypto(stock_ticker)}")

    # Download stock data
    stock_df = yf.download(
        [stock_ticker],
        period='10y',
        interval='1d',
        group_by='ticker',
    )
    stock_df = yfinance_service.extract_ticker_df(df=stock_df, ticker=stock_ticker)

    if len(stock_df) > 0:
        print(f"Downloaded {len(stock_df)} days of data")

        # Apply regression with is_crypto=False (default)
        # Match fundamentals_update.py: window = len(df)-1, future = len(df)//10
        window = len(stock_df) - 1
        future = len(stock_df) // 10  # 1/10th of 10 years = ~1 year forecast
        stock_df = regression_utility.add_close_window_growths(
            stock_df,
            window=window,
            future=future,
            is_crypto=False
        )

        print(f"\nStock regression results:")
        print(f"Growth columns: {[col for col in stock_df.columns if 'Growth' in col]}")
        print(f"Last actual close: {stock_df['Close'].dropna().iloc[-1]:.2f}")
        print(f"Last growth value: {stock_df['Growth'].dropna().iloc[-1]:.2f}")
        print(f"Growth lower: {stock_df['Growth Lower'].dropna().iloc[-1]:.2f}")
        print(f"Growth upper: {stock_df['Growth Upper'].dropna().iloc[-1]:.2f}")

        # Check if future dates exclude weekends (they should for stocks)
        future_dates = stock_df.index[-future:]
        last_actual_date = stock_df['Close'].dropna().index[-1]
        final_prediction_date = stock_df['Growth'].dropna().index[-1]

        print(f"\nDate information:")
        print(f"Last actual data date: {last_actual_date.strftime('%Y-%m-%d (%A)')}")
        print(f"Final prediction date: {final_prediction_date.strftime('%Y-%m-%d (%A)')}")
        print(f"Days into future: {(final_prediction_date - last_actual_date).days}")
        print(f"\nFuture dates (last 5): {list(future_dates[-5:])}")
        print(f"Includes weekends: {any(d.weekday() >= 5 for d in future_dates)}")

        # Generate visual plot
        plot_path = plot_utility.plot_bands_by_labels(
            df=stock_df,
            ticker=stock_ticker,
            title=f"{stock_ticker} - EXPONENTIAL REGRESSION (Stock)",
            subtitle=f"Exponential regression with business-day forecast",
            labels=[
                'Growth Upper',
                'Growth',
                'Growth Lower',
            ],
            yscale='log',  # Log scale for stocks to show exponential growth better
            today=-1-future,
            close_only=True,
        )
        print(f"\n📊 Stock plot saved to: {plot_path}")

        return plot_path
    else:
        print("No data downloaded for stock")
        return None


if __name__ == '__main__':
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    print("=" * 80)
    print("CRYPTOCURRENCY vs STOCK REGRESSION COMPARISON TEST")
    print("=" * 80)

    crypto_plot = test_crypto_regression()
    stock_plot = test_stock_regression()

    print("\n" + "=" * 80)
    print("✓ Tests completed!")
    print("=" * 80)

    if crypto_plot:
        print(f"\n📈 CRYPTO PLOT (Linear Regression):  {os.path.abspath(crypto_plot)}")
    if stock_plot:
        print(f"📈 STOCK PLOT (Exponential Regression): {os.path.abspath(stock_plot)}")

    print("\n💡 Key differences to observe in plots:")
    print("   • Crypto: Linear trend line (straight line on linear scale)")
    print("   • Stock:  Exponential trend line (straight line on log scale)")
    print("   • Crypto: Future dates include weekends (continuous)")
    print("   • Stock:  Future dates skip weekends (gaps visible)")
    print("=" * 80)

