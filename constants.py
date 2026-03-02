from enum import Enum


output_directory = '/home/moritz/PycharmProjects/StonksTelegramBot/output/'


class DictionaryKeys(Enum):
    too_short = 'too_short'
    peg_ratio_too_high = 'peg_ratio_too_high'
    price_target_too_low = 'price_target_too_low'
    growth_too_low = 'growth_too_low'
    too_expensive = 'too_expensive'
    not_enough_undervaluation = 'not_enough_undervaluation'
    no_technicals = 'no_momentum'
    pe_ratio_too_high = 'pe_ratio_too_high'
    value_too_low = 'value_too_low'
    ev_to_ebitda_too_high = 'ev_to_ebitda_too_high'


class CommonDictionaryKey(Enum):
    """Base class for dictionary keys that can be used together"""
    pass


class DictionaryKeysNew(CommonDictionaryKey):
    too_short = 'Too short'
    no_growth = 'No growth'
    too_expensive = 'Too expensive'
    no_fundamentals = 'No fundamentals'
    no_technicals = 'No technicals'


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
