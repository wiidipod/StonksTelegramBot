import numpy as np
from scipy.optimize import linprog
from scipy.sparse import vstack, hstack, eye, csr_matrix
import pandas as pd

from yfinance_service import P


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


def get_date(date, offset):
    weekends = offset // 5
    return date + pd.DateOffset(days=offset + weekends * 2)


def add_window_growths(df, window=1250, future=0):
    growth_h = pd.Series(index=df.index)
    growth_lower_h = pd.Series(index=df.index)
    growth_upper_h = pd.Series(index=df.index)
    growth_l = pd.Series(index=df.index)
    growth_lower_l = pd.Series(index=df.index)
    growth_upper_l = pd.Series(index=df.index)

    slope_h = 0.0
    intercept_h = 0.0
    rmsa_h = 0.0
    slope_l = 0.0
    intercept_l = 0.0
    rmsa_l = 0.0

    for start_index in range(len(df) - window):
        end_index = start_index + window
        date = df.index[end_index]

        sub_df = df.iloc[start_index:end_index]
        g_h, g_l_h, g_u_h, slope_h, intercept_h, rmsa_h = get_growth_and_final_coefficients(sub_df[P.H.value])
        g_l, g_l_l, g_u_l, slope_l, intercept_l, rmsa_l = get_growth_and_final_coefficients(sub_df[P.L.value])

        growth_h[date] = g_h
        growth_lower_h[date] = g_l_h
        growth_upper_h[date] = g_u_h
        growth_l[date] = g_l
        growth_lower_l[date] = g_l_l
        growth_upper_l[date] = g_u_l

    last_date = df.index[-1]
    future_dates = [get_date(last_date, i + 1) for i in range(future)]

    future_growth_h = pd.Series(index=future_dates)
    future_growth_lower_h = pd.Series(index=future_dates)
    future_growth_upper_h = pd.Series(index=future_dates)
    future_growth_l = pd.Series(index=future_dates)
    future_growth_lower_l = pd.Series(index=future_dates)
    future_growth_upper_l = pd.Series(index=future_dates)

    for i, n in enumerate(range(window, window + future)):
        fit_h = slope_h * n + intercept_h
        fit_l = slope_l * n + intercept_l
        future_growth_h[future_dates[i]] = np.exp(fit_h)
        future_growth_lower_h[future_dates[i]] = np.exp(fit_h - rmsa_h)
        future_growth_upper_h[future_dates[i]] = np.exp(fit_h + rmsa_h)
        future_growth_l[future_dates[i]] = np.exp(fit_l)
        future_growth_lower_l[future_dates[i]] = np.exp(fit_l - rmsa_l)
        future_growth_upper_l[future_dates[i]] = np.exp(fit_l + rmsa_l)

    df = df.reindex(df.index.union(future_dates))

    df['Growth (High)'] = pd.concat([growth_h, future_growth_h])
    df['Growth Lower (High)'] = pd.concat([growth_lower_h, future_growth_lower_h])
    df['Growth Upper (High)'] = pd.concat([growth_upper_h, future_growth_upper_h])
    df['Growth (Low)'] = pd.concat([growth_l, future_growth_l])
    df['Growth Lower (Low)'] = pd.concat([growth_lower_l, future_growth_lower_l])
    df['Growth Upper (Low)'] = pd.concat([growth_upper_l, future_growth_upper_l])

    return df


def add_growths(df, future=0):
    growth_h, growth_lower_h, growth_upper_h, slope_h, intercept_h, rmsa_h = get_growths_and_final_coefficients(df[P.H.value])
    growth_l, growth_lower_l, growth_upper_l, slope_l, intercept_l, rmsa_l = get_growths_and_final_coefficients(df[P.L.value])

    last_date = df.index[-1]
    future_dates = [get_date(last_date, i + 1) for i in range(future)]

    new_growth_h = []
    new_growth_lower_h = []
    new_growth_upper_h = []
    new_growth_l = []
    new_growth_lower_l = []
    new_growth_upper_l = []

    for i in range(len(df), len(df) + future):
        fit_h = slope_h * i + intercept_h
        fit_l = slope_l * i + intercept_l
        new_growth_h.append(np.exp(fit_h))
        new_growth_lower_h.append(np.exp(fit_h - rmsa_h))
        new_growth_upper_h.append(np.exp(fit_h + rmsa_h))
        new_growth_l.append(np.exp(fit_l))
        new_growth_lower_l.append(np.exp(fit_l - rmsa_l))
        new_growth_upper_l.append(np.exp(fit_l + rmsa_l))

    new_growth_h = pd.Series(new_growth_h, index=future_dates)
    new_growth_lower_h = pd.Series(new_growth_lower_h, index=future_dates)
    new_growth_upper_h = pd.Series(new_growth_upper_h, index=future_dates)
    new_growth_l = pd.Series(new_growth_l, index=future_dates)
    new_growth_lower_l = pd.Series(new_growth_lower_l, index=future_dates)
    new_growth_upper_l = pd.Series(new_growth_upper_l, index=future_dates)

    df = df.reindex(df.index.union(future_dates))

    df['Growth (High)'] = pd.concat([growth_h, new_growth_h])
    df['Growth Lower (High)'] = pd.concat([growth_lower_h, new_growth_lower_h])
    df['Growth Upper (High)'] = pd.concat([growth_upper_h, new_growth_upper_h])
    df['Growth (Low)'] = pd.concat([growth_l, new_growth_l])
    df['Growth Lower (Low)'] = pd.concat([growth_lower_l, new_growth_lower_l])
    df['Growth Upper (Low)'] = pd.concat([growth_upper_l, new_growth_upper_l])

    return df


def get_growth_and_final_coefficients(series):
    series_log = np.log(series)
    n = len(series_log)
    sum_y = np.sum(series_log)
    sum_xy = np.sum(np.arange(n) * series_log)
    sum_x = n * (n - 1.0) / 2.0
    sum_xx = (n - 1.0) * n * (2.0 * n - 1.0) / 6.0
    denominator = sum_xx - (sum_x ** 2.0) / n

    if denominator == 0:
        slope = 0.0
        intercept = sum_y / n
    else:
        slope = (sum_xy - (sum_x * sum_y) / n) / denominator
        intercept = (sum_y / n) - slope * (sum_x / n)

    fit = slope * np.arange(n) + intercept
    rmsa = np.sqrt(np.sum((series_log - fit) ** 2.0) / n)
    growth = np.exp(fit[-1])
    growth_lower = np.exp(fit[-1] - rmsa)
    growth_upper = np.exp(fit[-1] + rmsa)

    return growth, growth_lower, growth_upper, slope, intercept, rmsa


def get_growths_and_final_coefficients(series):
    series_log = np.log(series)
    growth = pd.Series(index=series.index)
    growth_lower = pd.Series(index=series.index)
    growth_upper = pd.Series(index=series.index)
    n = 0
    sum_y = 0.0
    sum_xy = 0.0
    slope = 0.0
    intercept = 0.0
    rmsa = 0.0

    for i, (date, y) in enumerate(series_log.items()):
        n += 1.0
        sum_y += y
        sum_xy += i * y
        sum_x = n * (n - 1.0) / 2.0
        sum_xx = (n - 1.0) * n * (2.0 * n - 1.0) / 6.0
        denominator = sum_xx - (sum_x ** 2.0) / n

        if denominator == 0:
            slope = 0.0
            intercept = sum_y / n
        else:
            slope = (sum_xy - (sum_x * sum_y) / n) / denominator
            intercept = (sum_y / n) - slope * (sum_x / n)

        fit = slope * i + intercept
        rmsa = ((rmsa ** 2.0 * i + (y - fit) ** 2.0) / (i + 1.0)) ** 0.5
        growth[date] = np.exp(fit)
        growth_lower[date] = np.exp(fit - rmsa)
        growth_upper[date] = np.exp(fit + rmsa)

    return growth, growth_lower, growth_upper, slope, intercept, rmsa


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
