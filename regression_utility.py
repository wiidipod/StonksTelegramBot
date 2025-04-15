import numpy as np
from scipy.optimize import linprog
from scipy.sparse import vstack, hstack, eye, csr_matrix



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
    A_ub = hstack([-X, -eye(len(closes))])
    A_lb = hstack([X, -eye(len(closes))])
    b_ub = -np.log(closes)
    b_lb = np.log(closes)
    A = vstack([A_ub, A_lb])
    b = np.hstack([b_ub, b_lb])
    res = linprog(c, A_ub=csr_matrix(A), b_ub=b, method='highs')

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


def get_daily_growths(prices):
    prices_log = np.log(prices)
    growth = []
    upper_growth = []
    lower_growth = []
    double_upper_growth = []
    double_lower_growth = []
    mae = 0.0
    rmsa = 0.0

    n = 0
    sum_y = 0.0
    sum_xy = 0.0

    for i, y in enumerate(prices_log):
        n += 1
        sum_y += y
        sum_xy += i * y

        if n >= 2:
            sum_x = n * (n - 1) / 2
            sum_xx = (n - 1) * n * (2 * n - 1) / 6
            denominator = sum_xx - (sum_x ** 2) / n

            if denominator != 0:
                slope = (sum_xy - (sum_x * sum_y) / n) / denominator
                intercept = (sum_y / n) - slope * (sum_x / n)
            else:
                slope = 0.0
                intercept = sum_y / n
        else:
            slope = 0.0
            intercept = y
        mae = (mae * i + abs(y - (slope * i + intercept))) / (i + 1.0)
        rmsa = ((rmsa**2 * i + (y - (slope * i + intercept))**2) / (i + 1.0))**0.5
        growth.append(slope * i + intercept)
        lower_growth.append(slope * i + intercept - rmsa)
        upper_growth.append(slope * i + intercept + 1.0 * rmsa)
        double_lower_growth.append(slope * i + intercept - 1.0 / 3.0 * rmsa)
        double_upper_growth.append(slope * i + intercept + 1.0 / 3.0 * rmsa)

    print(f"MAE: {mae}, MSA: {rmsa}")
    return np.exp(growth), np.exp(lower_growth), np.exp(upper_growth), np.exp(double_lower_growth), np.exp(double_upper_growth), np.exp([slope * i + intercept for i in range(len(prices))])


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
