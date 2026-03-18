# StonksTelegramBot – Agent Guide

## Architecture Overview

A Telegram bot that performs technical/fundamental stock analysis and pushes charts + messages to subscribers. Two runtime modes:

- **Interactive bot**: `poller.py` → `telegram_service.py` handles commands live (`/analyze`, `/subscribe`, `/stoploss`, etc.)
- **Batch update scripts**: standalone `__main__` scripts that run analysis and push results via Telegram: `update.py`, `hype_update.py`, `subscriptions_update.py`, `reddit_update.py`, `alchemy.py`, `fundamentals_update_new.py`

## Key Files & Responsibilities

| File | Role |
|---|---|
| `telegram_service.py` | Bot setup, all command handlers, message/plot sending helpers |
| `fundamentals_update_new.py` | Core per-ticker analysis pipeline (`analyze()`, `get_plot_path_and_message_for()`) |
| `yfinance_service.py` | All market data fetching via `yfinance`; `extract_ticker_df()` normalises multi-ticker downloads |
| `ticker_service.py` | Scrapes Wikipedia for index constituents; classifies tickers (`is_stock`, `is_crypto`, `is_future`) |
| `regression_utility.py` | Log-scale L1 regression via `scipy.optimize.linprog` (not least-squares); `add_close_window_growths()` adds growth bands to a DataFrame |
| `ta_utility.py` | RSI, MACD, EMA/SMA wrappers around the `ta` library; `add_*` functions mutate DataFrames in-place |
| `plot_utility.py` | Generates PNG charts with matplotlib/mplfinance; all plots saved to `output/` |
| `message_utility.py` | Formats Telegram messages; uses `telegramify_markdown` (not raw MarkdownV2 escaping) |
| `alchemy.py` | Multi-factor score: TEV, ROA, Book/Market, FCF yield, 3M/6M momentum |
| `pe_utility.py` | Scrapes PE ratios with Selenium headless Chrome; cached in `pe_ratios.csv` |
| `constants.py` | Shared enums (`DictionaryKeysNew`, `TechnicalsKeys`, `GrowthKeys`) and `output_directory` |

## Hardcoded Paths (must match deployment environment)

Several files hard-reference the Linux server path `/home/moritz/PycharmProjects/StonksTelegramBot/`:
- `telegram_service.py`: `subscribers_file`, `token` file path
- `message_utility.py`: `subscriptions_file`
- `constants.py`: `output_directory`

When running locally, update these or symlink accordingly.

## Data & State Files

- `token` – Telegram bot token (plain text, one line)
- `subscribers.txt` – newline-separated Telegram chat IDs
- `subscriptions.txt` – one entry per line: `chat_id$TICKER` (e.g. `123456$AAPL`)
- `pe_ratios.csv` – cached industry PE ratios (`Industry,PE_Ratio` columns + `S&P 500` row)
- `output/` – all generated PNG plots land here

## Core Analysis Pipeline

`fundamentals_update_new.analyze(df, ticker, future, full, pe_ratios)` populates a `DictionaryKeysNew` dict with `True`/`False` per rejection reason:

```
too_short → no_technicals → no_growth → too_expensive → no_fundamentals → no_multibagger
```

A ticker passes if **all values are `False`**. Use `has_buy_signal(dictionary)` to check.

`future` is always computed as `len(df) // 10` (≈ 1 year for 10 years of daily data).

## Ticker Classification Pattern

```python
from ticker_service import is_stock, is_crypto, is_future

is_crypto("BTC-EUR")   # True  – ends in -USD or -EUR
is_future("GC=F")      # True  – ends in =F
# Indices start with ^, e.g. '^GSPC'
```

Crypto regression uses calendar days for future dates; stocks use `pd.bdate_range`.

## Running Batch Scripts

```bash
python poller.py                          # start interactive bot
python subscriptions_update.py            # send analysis for first subscriber only
python subscriptions_update.py --all      # send to every subscriber
python hype_update.py                     # ATH-quarter analysis for hype tickers
python update.py                          # regression update for major indices
python alchemy.py                         # multi-factor stock screener
```

## Message Formatting Convention

Do **not** manually escape Telegram MarkdownV2 characters. Instead, write standard Markdown and pass through `telegramify_markdown.markdownify()` (wrapped in `message_utility.escape_characters_for_markdown()`). Raw code blocks use triple backticks in the source string.

## Old vs New Fundamentals

`fundamentals_update.py` is the legacy pipeline; `fundamentals_update_new.py` is active. `backtest.py` still imports the old module. When extending analysis, target `fundamentals_update_new.py`.

## External Data Sources

- **Yahoo Finance** (`yfinance`) – all OHLCV data and fundamental info
- **Wikipedia** – index constituents (scraped by `ticker_service.get_tickers()`)
- **Finviz / Yahoo recommendations API / FMP** – competitor discovery (fallback chain in `fundamental_analysis.py`)
- **fullratio.com + multpl.com** – industry and S&P 500 PE ratios (Selenium scrape in `pe_utility.py`)

