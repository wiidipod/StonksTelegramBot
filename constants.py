import os
from enum import Enum


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
output_directory = os.path.join(PROJECT_DIR, 'output') + os.sep
subscribers_file = os.path.join(PROJECT_DIR, 'subscribers.txt')
subscriptions_file = os.path.join(PROJECT_DIR, 'subscriptions.txt')
group_subscriptions_file = os.path.join(PROJECT_DIR, 'group_subscriptions.txt')
token_file = os.path.join(PROJECT_DIR, 'token')
group_counts_file = os.path.join(PROJECT_DIR, 'group_counts.json')
msci_world_csv = os.path.join(PROJECT_DIR, 'EUNL_holdings.csv')

DEFAULT_GROUPS = [
    's_p_500',
    'euro_stoxx_50',
    'dax',
    'msci_world',
    'cryptocurrency_usd',
    'cryptocurrency_eur',
    'precious_metals',
    'energy',
    'stock_market_indices',
    'future',
    'letf',
]


class CommonDictionaryKey(Enum):
    """Base class for dictionary keys that can be used together"""
    pass


class DictionaryKeysNew(CommonDictionaryKey):
    too_short = 'Too short'
    no_growth = 'No growth'
    too_expensive = 'Too expensive'
    no_fundamentals = 'No fundamentals'
    no_technicals = 'No technicals'
    no_multibagger = 'No multibagger'


class UndervaluedKey(CommonDictionaryKey):
    undervalued = 'undervalued'


class TechnicalsKeys(str, Enum):
    macd = 'MACD'
    macd_signal = 'MACD Signal'
    macd_diff = 'MACD Diff'
    rsi = 'RSI'
    sma = 'SMA-'
    ema = 'EMA-'


class GrowthKeys(Enum):
    growth = 'Growth'
    growth_lower = 'Growth Lower'
    growth_upper = 'Growth Upper'
