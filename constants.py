from enum import Enum


output_directory = '/home/moritz/PycharmProjects/StonksTelegramBot/output/'


class DictionaryKeys(Enum):
    too_short = 'too_short'
    peg_ratio_too_high = 'peg_ratio_too_high'
    price_target_too_low = 'price_target_too_low'
    growth_too_low = 'growth_too_low'
    too_expensive = 'too_expensive'
    not_enough_undervaluation = 'not_enough_undervaluation'
