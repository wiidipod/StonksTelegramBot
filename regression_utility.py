import numpy as np


def get_fit(closes):
    try:
        fit, residuals, rank, singular_values, rcond = np.polyfit(range(len(closes)), np.log(closes), 1, full=True)
    except:
        return 0, 0, 0
    factor = np.exp(fit[1])
    base = np.exp(fit[0])
    error_factor = np.exp((residuals[0] / len(closes)) ** 0.5)
    return factor, base, error_factor


def get_growth(length, factor, base, multiplier=1.0):
    return [factor * base ** i * multiplier for i in range(length)]


def get_growths(closes, future=0):
    factor, base, error_factor = get_fit(closes)

    growth = get_growth(len(closes) + future, factor, base)
    lower_growth = [g / error_factor for g in growth]
    upper_growth = [g * error_factor for g in growth]
    lower_border = [min(c / g for c, g in zip(closes, growth)) * g for g in growth]
    upper_border = [max(c / g for c, g in zip(closes, growth)) * g for g in growth]

    return growth, lower_growth, upper_growth, lower_border, upper_border
