import ticker_service
import yfinance_service
import regression_utility
from tqdm import tqdm
import scipy.stats


def print_analysis(gains, name, switches=[]):
    print(f'    {name}')
    print(f'        average: {scipy.stats.gmean(gains) * 100.0 - 100.0:8.2f} %')
    print(f'        min:     {min(gains) * 100.0 - 100.0:8.2f} %')
    print(f'        max:     {max(gains) * 100.0 - 100.0:8.2f} %')
    if len(switches) != 0:
        print(f'        average switches: {scipy.stats.tmean(switches):4.0f}')
        print(f'        min switches:     {min(switches):4.0f}')
        print(f'        max switches:     {max(switches):4.0f}')


def exit_triple(
        enter_price_dict,
        etf_closes_dict,
        etf_index_dict,
        gain_dict,
        index_close,
        key,
        l,
        switch_count_dict,
        today,
        u,
        rsi,
):
    etf_index = etf_index_dict[key]
    if etf_index == 2 and l < index_close[-1] and rsi > 30:
        gain_dict[key] *= etf_closes_dict[key][etf_index][today] / enter_price_dict[key]
        enter_price_dict[key] = 0.0
        switch_count_dict[key] += 1
    elif etf_index == 1 and ((l > index_close[-1] and rsi < 70) or (u < index_close[-1] and rsi > 30)):
        gain_dict[key] *= etf_closes_dict[key][etf_index][today] / enter_price_dict[key]
        enter_price_dict[key] = 0.0
        switch_count_dict[key] += 1
    elif etf_index == 0 and u > index_close[-1] and rsi < 70:
        gain_dict[key] *= etf_closes_dict[key][etf_index][today] / enter_price_dict[key]
        enter_price_dict[key] = 0.0
        switch_count_dict[key] += 1


def enter_triple(
        enter_price_dict,
        etf_closes_dict,
        etf_index_dict,
        index_close,
        key,
        l,
        today,
        u
):
    if enter_price_dict[key] == 0.0:
        if l > index_close[-1]:
            enter_price_dict[key] = etf_closes_dict[key][2][today]
            etf_index_dict[key] = 2
        elif u > index_close[-1]:
            enter_price_dict[key] = etf_closes_dict[key][1][today]
            etf_index_dict[key] = 1
        else:
            enter_price_dict[key] = etf_closes_dict[key][0][today]
            etf_index_dict[key] = 0


def initialize_dictionaries(etf_closes_dict):
    enter_price_dict = {key: 0.0 for key in etf_closes_dict}
    etf_index_dict = {key: 0 for key in etf_closes_dict}
    gain_dict = {key: 1.0 for key in etf_closes_dict}
    switch_count_dict = {key: 0 for key in etf_closes_dict}
    return enter_price_dict, etf_index_dict, gain_dict, switch_count_dict


def try_strategies(
        close,
        etf_closes_dict,
        backtest_start_index,
        growth_dict,
        lower_growth_dict,
        upper_growth_dict,
        rsi_dict,
        horizon_days=1250,
        backtest_days=2500,
        use_tqdm=False,
):
    enter_price_dict, etf_index_dict, gain_dict, switch_count_dict = initialize_dictionaries(etf_closes_dict)

    for i in (tqdm(range(horizon_days))) if use_tqdm else range(horizon_days):
        today = backtest_start_index + i
        index_close = close[today - backtest_days:today]
        # index_close = close[:today]

        if today in growth_dict:
            g = growth_dict[today]
            l = lower_growth_dict[today]
            u = upper_growth_dict[today]
            # dl = double_lower_growth_dict[today]
            # du = double_upper_growth_dict[today]
            rsi = rsi_dict[today]
        else:
            growth, lower_growth, upper_growth, double_lower_growth, double_upper_growth = regression_utility.get_growths(index_close)
            g = growth[-1]
            l = lower_growth[-1]
            u = upper_growth[-1]
            growth_dict[today] = g
            lower_growth_dict[today] = l
            upper_growth_dict[today] = u
            # rsi = RSIIndicator(pd.Series(index_close)).rsi().iloc[-1]
            rsi = 50.0
            rsi_dict[today] = rsi

        for key in etf_closes_dict:
            strategy_count = len(etf_closes_dict[key]) - 1

            try_single_strategy(enter_price_dict, etf_closes_dict, key, strategy_count, today)

            try_double_strategy(
                enter_price_dict,
                etf_closes_dict,
                etf_index_dict,
                gain_dict,
                l,
                g,
                u,
                index_close,
                key,
                strategy_count,
                switch_count_dict,
                today,
                rsi,
            )

            try_triple_strategy(
                enter_price_dict,
                etf_closes_dict,
                etf_index_dict,
                gain_dict,
                index_close,
                key,
                l,
                g,
                u,
                strategy_count,
                switch_count_dict,
                today,
                rsi,
            )

            try_quadruple_strategy(
                enter_price_dict,
                etf_closes_dict,
                etf_index_dict,
                gain_dict,
                g,
                index_close,
                key,
                l,
                strategy_count,
                switch_count_dict,
                today,
                u,
                rsi,
            )

    # final exit
    final_exit(backtest_start_index, enter_price_dict, etf_closes_dict, etf_index_dict, gain_dict, horizon_days)

    return gain_dict, switch_count_dict, growth_dict, lower_growth_dict, upper_growth_dict, rsi_dict


def try_quadruple_strategy(
        enter_price_dict,
        etf_closes_dict,
        etf_index_dict,
        gain_dict,
        g,
        index_close,
        key,
        l,
        strategy_count,
        switch_count_dict,
        today,
        u,
        rsi,
):
    if strategy_count == 4:
        enter_quadruple(
            enter_price_dict,
            etf_closes_dict,
            etf_index_dict,
            g,
            index_close,
            key,
            l,
            today,
            u
        )

        exit_quadruple(
            enter_price_dict,
            etf_closes_dict,
            etf_index_dict,
            gain_dict,
            g,
            index_close,
            key,
            l,
            switch_count_dict,
            today,
            u,
            rsi,
        )


def try_triple_strategy(
        enter_price_dict,
        etf_closes_dict,
        etf_index_dict,
        gain_dict,
        index_close,
        key,
        l,
        g,
        u,
        strategy_count,
        switch_count_dict,
        today,
        rsi,
):
    if strategy_count == 3:
        b1 = l
        b2 = u
        if etf_closes_dict[key][-1] == 'lg':
            b2 = g
        if etf_closes_dict[key][-1] == 'gu':
            b1 = g

        enter_triple(
            enter_price_dict,
            etf_closes_dict,
            etf_index_dict,
            index_close,
            key,
            b1,
            today,
            b2
        )

        exit_triple(
            enter_price_dict,
            etf_closes_dict,
            etf_index_dict,
            gain_dict,
            index_close,
            key,
            b1,
            switch_count_dict,
            today,
            b2,
            rsi,
        )


def try_double_strategy(
        enter_price_dict,
        etf_closes_dict,
        etf_index_dict,
        gain_dict,
        l,
        g,
        u,
        index_close,
        key,
        strategy_count,
        switch_count_dict,
        today,
        rsi,
):
    if strategy_count == 2:
        b = g
        if etf_closes_dict[key][-1] == 'l':
            b = l
        if etf_closes_dict[key][-1] == 'u':
            b = u

        enter_double(
            enter_price_dict,
            etf_closes_dict,
            etf_index_dict,
            b,
            index_close,
            key,
            today
        )

        exit_double(
            enter_price_dict,
            etf_closes_dict,
            etf_index_dict,
            gain_dict,
            b,
            index_close,
            key,
            switch_count_dict,
            today,
            rsi,
        )


def try_single_strategy(enter_price_dict, etf_closes_dict, key, strategy_count, today):
    if strategy_count == 1:
        if enter_price_dict[key] == 0.0:
            enter_price_dict[key] = etf_closes_dict[key][0][today]


def exit_quadruple(
        enter_price_dict,
        etf_closes_dict,
        etf_index_dict,
        gain_dict,
        g,
        index_close,
        key,
        l,
        switch_count_dict,
        today,
        u,
        rsi,
):
    etf_index = etf_index_dict[key]
    if etf_index == 3 and l < index_close[-1] and rsi > 30:
        gain_dict[key] *= etf_closes_dict[key][etf_index][today] / enter_price_dict[key]
        enter_price_dict[key] = 0.0
        switch_count_dict[key] += 1
    elif etf_index == 2 and ((l > index_close[-1] and rsi < 70) or (g < index_close[-1] and rsi > 30)):
        gain_dict[key] *= etf_closes_dict[key][etf_index][today] / enter_price_dict[key]
        enter_price_dict[key] = 0.0
        switch_count_dict[key] += 1
    elif etf_index == 1 and ((g > index_close[-1] and rsi < 70) or (u < index_close[-1] and rsi > 30)):
        gain_dict[key] *= etf_closes_dict[key][etf_index][today] / enter_price_dict[key]
        enter_price_dict[key] = 0.0
        switch_count_dict[key] += 1
    elif etf_index == 0 and u > index_close[-1] and rsi < 70:
        gain_dict[key] *= etf_closes_dict[key][etf_index][today] / enter_price_dict[key]
        enter_price_dict[key] = 0.0
        switch_count_dict[key] += 1


def enter_quadruple(
        enter_price_dict,
        etf_closes_dict,
        etf_index_dict,
        g,
        index_close,
        key,
        l,
        today,
        u
):
    if enter_price_dict[key] == 0.0:
        if l > index_close[-1]:
            enter_price_dict[key] = etf_closes_dict[key][3][today]
            etf_index_dict[key] = 3
        elif g > index_close[-1]:
            enter_price_dict[key] = etf_closes_dict[key][2][today]
            etf_index_dict[key] = 2
        elif u > index_close[-1]:
            enter_price_dict[key] = etf_closes_dict[key][1][today]
            etf_index_dict[key] = 1
        else:
            enter_price_dict[key] = etf_closes_dict[key][0][today]
            etf_index_dict[key] = 0


def final_exit(backtest_start_index, enter_price_dict, etf_closes_dict, etf_index_dict, gain_dict, horizon_days):
    for key in etf_closes_dict:
        etf_index = etf_index_dict[key]
        if enter_price_dict[key] > 0.0:
            gain_dict[key] *= etf_closes_dict[key][etf_index][backtest_start_index + horizon_days] / enter_price_dict[key]


def exit_double(
        enter_price_dict,
        etf_closes_dict,
        etf_index_dict,
        gain_dict,
        g,
        index_close,
        key,
        switch_count_dict,
        today,
        rsi,
):
    etf_index = etf_index_dict[key]
    if etf_index == 1 and g < index_close[-1] and rsi > 30:
        gain_dict[key] *= etf_closes_dict[key][etf_index][today] / enter_price_dict[key]
        enter_price_dict[key] = 0.0
        switch_count_dict[key] += 1
    elif etf_index == 0 and g > index_close[-1] and rsi < 70:
        gain_dict[key] *= etf_closes_dict[key][etf_index][today] / enter_price_dict[key]
        enter_price_dict[key] = 0.0
        switch_count_dict[key] += 1


def enter_double(
        enter_price_dict,
        etf_closes_dict,
        etf_index_dict,
        g,
        index_close,
        key,
        today
):
    if enter_price_dict[key] == 0.0:
        if g > index_close[-1]:
            enter_price_dict[key] = etf_closes_dict[key][1][today]
            etf_index_dict[key] = 1
        else:
            enter_price_dict[key] = etf_closes_dict[key][0][today]
            etf_index_dict[key] = 0


if __name__ == '__main__':
    index_tickers = [
        "^GSPC",
        # "^NDX",
        # "^GDAXI",
        # "BTC-USD",
    ]

    closes = yfinance_service.get_closes(index_tickers)

    for ticker in index_tickers:
        close = closes[ticker]
        etf_tickers = ticker_service.get_etf_tickers(ticker)

        backtest_days = 2500
        horizon_days = 5 * 250

        growth, lower_growth, upper_growth, double_lower_growth, double_upper_growth = regression_utility.get_growths(close, future=0)
        # plot_utility.plot(ticker, [
        #     close,
        #     growth,
        #     lower_growth,
        #     upper_growth,
        #     double_lower_growth,
        #     double_upper_growth,
        # ])
        print(f'{ticker}:')

        print(f'    upper border: {double_upper_growth[-1]:16.8f}%')
        print(f'    upper growth: {upper_growth[-1]:16.8f}%')
        print(f'    growth:       {growth[-1]:16.8f}%')
        print(f'    lower growth: {lower_growth[-1]:16.8f}%')
        print(f'    lower border: {double_lower_growth[-1]:16.8f}%')

        etf_closes = yfinance_service.get_closes(etf_tickers)

        etf_closes_0x = [1.0] * backtest_days
        etf_closes_1x = etf_closes[etf_tickers[0]]
        etf_closes_2x = etf_closes[etf_tickers[1]]
        etf_closes_3x = etf_closes[etf_tickers[2]]

        etf_closes_dict = {
            '0x': [etf_closes_0x, ''],
            '1x': [etf_closes_1x, ''],
            '2x': [etf_closes_2x, ''],
            '3x': [etf_closes_3x, ''],
            '1x_l_2x': [etf_closes_1x, etf_closes_2x, 'l'],
            '1x_g_2x': [etf_closes_1x, etf_closes_2x, 'g'],
            '1x_u_2x': [etf_closes_1x, etf_closes_2x, 'u'],
            '2x_l_3x': [etf_closes_2x, etf_closes_3x, 'l'],
            '2x_g_3x': [etf_closes_2x, etf_closes_3x, 'g'],
            '2x_u_3x': [etf_closes_2x, etf_closes_3x, 'u'],
            '1x_l_3x': [etf_closes_1x, etf_closes_3x, 'l'],
            '1x_g_3x': [etf_closes_1x, etf_closes_3x, 'g'],
            '1x_u_3x': [etf_closes_1x, etf_closes_3x, 'u'],
            '0x_l_1x': [etf_closes_0x, etf_closes_1x, 'l'],
            '0x_g_1x': [etf_closes_0x, etf_closes_1x, 'g'],
            '0x_u_1x': [etf_closes_0x, etf_closes_1x, 'u'],
            '0x_l_2x': [etf_closes_0x, etf_closes_2x, 'l'],
            '0x_g_2x': [etf_closes_0x, etf_closes_2x, 'g'],
            '0x_u_2x': [etf_closes_0x, etf_closes_2x, 'u'],
            '0x_l_3x': [etf_closes_0x, etf_closes_3x, 'l'],
            '0x_g_3x': [etf_closes_0x, etf_closes_3x, 'g'],
            '0x_u_3x': [etf_closes_0x, etf_closes_3x, 'u'],
            '0x_l_1x_g_2x': [etf_closes_0x, etf_closes_1x, etf_closes_2x, 'lg'],
            '0x_l_1x_u_2x': [etf_closes_0x, etf_closes_1x, etf_closes_2x, 'lu'],
            '0x_g_1x_u_2x': [etf_closes_0x, etf_closes_1x, etf_closes_2x, 'gu'],
            '0x_l_1x_g_3x': [etf_closes_0x, etf_closes_1x, etf_closes_3x, 'lg'],
            '0x_l_1x_u_3x': [etf_closes_0x, etf_closes_1x, etf_closes_3x, 'lu'],
            '0x_g_1x_u_3x': [etf_closes_0x, etf_closes_1x, etf_closes_3x, 'gu'],
            '0x_l_2x_g_3x': [etf_closes_0x, etf_closes_2x, etf_closes_3x, 'lg'],
            '0x_l_2x_u_3x': [etf_closes_0x, etf_closes_2x, etf_closes_3x, 'lu'],
            '0x_g_2x_u_3x': [etf_closes_0x, etf_closes_2x, etf_closes_3x, 'gu'],
            '1x_l_2x_g_3x': [etf_closes_1x, etf_closes_2x, etf_closes_3x, 'lg'],
            '1x_l_2x_u_3x': [etf_closes_1x, etf_closes_2x, etf_closes_3x, 'lu'],
            '1x_g_2x_u_3x': [etf_closes_1x, etf_closes_2x, etf_closes_3x, 'gu'],
            '0x_l_1x_g_2x_u_3x': [etf_closes_0x, etf_closes_1x, etf_closes_2x, etf_closes_3x, 'lgu'],
            # '1x_3x': [etf_closes_1x, etf_closes_3x],
            # '0x_1x': [etf_closes_0x, etf_closes_1x],
            # '0x_2x': [etf_closes_0x, etf_closes_2x],
            # '0x_3x': [etf_closes_0x, etf_closes_3x],
            # '0x_1x_2x': [etf_closes_0x, etf_closes_1x, etf_closes_2x],
            # '0x_1x_3x': [etf_closes_0x, etf_closes_1x, etf_closes_3x],
            # '0x_2x_3x': [etf_closes_0x, etf_closes_2x, etf_closes_3x],
            # '1x_2x_3x': [etf_closes_1x, etf_closes_2x, etf_closes_3x],
            # '0x_1x_2x_3x': [etf_closes_0x, etf_closes_1x, etf_closes_2x, etf_closes_3x],
        }

        gains_dict = {key: [] for key in etf_closes_dict}
        switches_dict = {key: [] for key in etf_closes_dict}
        growth_dict = {}
        lower_growth_dict = {}
        upper_growth_dict = {}
        rsi_dict = {}

        for i in range(backtest_days - horizon_days):
            print(f'    {i + 1} of {backtest_days - horizon_days}...')
            backtest_start_index = -horizon_days - i

            gain_dict, switch_count_dict, growth_dict, lower_growth_dict, upper_growth_dict, rsi_dict = try_strategies(
                close,
                etf_closes_dict,
                backtest_start_index,
                growth_dict,
                lower_growth_dict,
                upper_growth_dict,
                rsi_dict,
                horizon_days=horizon_days,
                backtest_days=backtest_days,
                use_tqdm=i==0,
            )

            for key in etf_closes_dict:
                gains_dict[key].append(gain_dict[key])
                switches_dict[key].append(switch_count_dict[key])

        print(f'{ticker}:')
        for key in gains_dict:
            print_analysis(gains_dict[key], key, switches_dict[key])
