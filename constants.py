from enum import Enum

class DictionaryKeys(Enum):
    too_short = 'too_short'
    peg_ratio_too_high = 'peg_ratio_too_high'
    price_target_too_low = 'price_target_too_low'
    growth_too_low = 'growth_too_low'
    too_expensive = 'too_expensive'
    not_52w_low = 'not_52w_low'
    not_enough_undervaluation = 'not_enough_undervaluation'
