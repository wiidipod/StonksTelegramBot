import numpy as np
from scipy.optimize import linprog


def get_fit(closes):
    # try:
    #     fit, residuals, rank, singular_values, rcond = np.polyfit(range(len(closes)), np.log(closes), 1, full=True)
    # except:
    #     return 0, 0, 0
    # factor = np.exp(fit[1])
    # base = np.exp(fit[0])
    # error_factor = np.exp((residuals[0] / len(closes)) ** 0.5)
    # return factor, base, error_factor

    X = np.vstack([np.arange(len(closes)), np.ones(len(closes))]).T
    c = np.hstack([np.zeros(2), np.ones(len(closes))])
    A_ub = np.hstack([-X, -np.eye(len(closes))])
    A_lb = np.hstack([X, -np.eye(len(closes))])
    b_ub = -np.log(closes)
    b_lb = np.log(closes)
    A = np.vstack([A_ub, A_lb])
    b = np.hstack([b_ub, b_lb])
    res = linprog(c, A_ub=A, b_ub=b, method='highs')

    if res.success:
        m, c = res.x[:2]
        y_pred = m * np.arange(len(closes)) + c
        absolute_errors = np.abs(y_pred - np.log(closes))
        mean_absolute_error = np.mean(absolute_errors)
        factor_new = np.exp(c)
        base_new = np.exp(m)
        error_factor_new = np.exp(mean_absolute_error)
        return factor_new, base_new, error_factor_new

    return 0, 0, 0


def get_growth(length, factor, base, multiplier=1.0):
    return [factor * base ** i * multiplier for i in range(length)]


def get_growths(closes, future=0):
    factor, base, error_factor = get_fit(closes)

    growth = get_growth(len(closes) + future, factor, base)
    lower_growth = [g / error_factor for g in growth]
    upper_growth = [g * error_factor for g in growth]
    double_lower_growth = [g / error_factor ** 2 for g in growth]
    double_upper_growth = [g * error_factor ** 2 for g in growth]
    # double_lower_growth = [min(c / g for c, g in zip(closes, growth)) * g for g in growth]
    # double_lower_growth = [max(c / g for c, g in zip(closes, growth)) * g for g in growth]

    return growth, lower_growth, upper_growth, double_lower_growth, double_upper_growth
