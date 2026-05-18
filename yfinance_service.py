import math
from enum import Enum

import yfinance as yf

from ticker_service import is_stock


class P(Enum):
    O = 'Open'
    H = 'High'
    L = 'Low'
    C = 'Close'


def _fetch_info(ticker):
    try:
        return yf.Ticker(ticker).info
    except Exception:
        return {}


def _is_valid_pos_number(value):
    return value is not None and value > 0.0 and not math.isnan(value)


def ticker_exists(ticker):
    try:
        df = yf.Ticker(ticker).history(period='5d')
        return not df.empty
    except Exception:
        return False


def extract_ticker_df(df, ticker):
    filtered_df = df[ticker].copy().dropna(subset=[P.H.value, P.L.value, P.C.value, P.O.value])
    return filtered_df[
        (filtered_df[P.H.value] > 0.0) &
        (filtered_df[P.L.value] > 0.0) &
        (filtered_df[P.C.value] > 0.0) &
        (filtered_df[P.O.value] > 0.0)
    ]


def get_industry_from_info(info):
    try:
        return info["industry"]
    except Exception:
        return ""


def get_recommendation_from_info(info):
    try:
        return info.get('recommendationKey')
    except Exception:
        return None


def get_pe_ratio_from_info(info):
    try:
        pe_ratio = info.get("trailingPE")
        return pe_ratio if _is_valid_pos_number(pe_ratio) else None
    except Exception:
        return None


def get_peg_ratio_from_info(info):
    try:
        peg_ratio = info.get("trailingPegRatio")
        return peg_ratio if _is_valid_pos_number(peg_ratio) else None
    except Exception:
        return None


def get_ev_to_ebitda_from_info(info):
    try:
        ev_to_ebitda = info.get("enterpriseToEbitda")
        return ev_to_ebitda if _is_valid_pos_number(ev_to_ebitda) else None
    except Exception:
        return None


def get_currency(ticker):
    return _fetch_info(ticker).get("currency", "")


def get_name_from_info(info, ticker='', mono=False, industry_pe_ratio=None):
    try:
        name = info.get("shortName") or info.get("longName") or ticker
    except Exception:
        info = {}
        name = ticker

    if mono:
        if is_stock(ticker):
            name = f'[{name}](https://valuecheck.io/analyze/{ticker})'
        else:
            name = f'[{name}](https://finance.yahoo.com/quote/{ticker})'
        info = {}

    try:
        industry = f"-{info['industry']}"
        if industry_pe_ratio is not None:
            industry += f" (P/E: {industry_pe_ratio})"
    except Exception:
        industry = ""

    try:
        country = f"-{info['country']}"
    except Exception:
        country = ""

    try:
        from message_utility import human_format
        market_cap = f"-MC: {human_format(info['marketCap'])}"
    except Exception:
        market_cap = ""

    if mono:
        return f'{name} (`{ticker}`)'
    else:
        return f'{name}({ticker}){industry}{country}{market_cap}'


def get_name(ticker, mono=False, industry_pe_ratio=None):
    info = _fetch_info(ticker)
    name = info.get("shortName") or info.get("longName") or ticker

    if mono:
        if is_stock(ticker):
            name = f'[{name}](https://valuecheck.io/analyze/{ticker})'
        else:
            name = f'[{name}](https://finance.yahoo.com/quote/{ticker})'
        return f'{name} (`{ticker}`)'

    try:
        industry = f"-{info['industry']}"
        if industry_pe_ratio is not None:
            industry += f"(P/E: {industry_pe_ratio})"
    except Exception:
        industry = ""

    try:
        country = f"-{info['country']}"
    except Exception:
        country = ""

    return f'{name}({ticker}){industry}{country}'


def get_price_target(ticker, low=True):
    try:
        price_targets = yf.Ticker(ticker).analyst_price_targets
        mean_pt = price_targets['mean']
        median_pt = price_targets['median']
        if _is_valid_pos_number(mean_pt) and _is_valid_pos_number(median_pt):
            return min(mean_pt, median_pt) if low else max(mean_pt, median_pt)
        if _is_valid_pos_number(mean_pt):
            return mean_pt
        if _is_valid_pos_number(median_pt):
            return median_pt
        return None
    except Exception:
        return None
