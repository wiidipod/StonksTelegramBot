import bs4 as bs
import requests


def get_tickers(
        source,
        attribute='id',
        name='constituents',
        table_index=0,
        column=0,
        replace_dots=False,
        exchange='',
        fill_digits=0,
        is_crypto=False,
        is_future=False,
):
    resp = requests.get(source)
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    tables = soup.find_all('table', {attribute: name})
    # tables = soup.find_all('table')
    table = tables[table_index]

    tickers = []

    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[column].text.strip()
        ticker = ticker.split(',')[0].split('[')[0].split(':')[-1].strip()

        if not ticker:
            continue

        if replace_dots:
            ticker = ticker.replace('.', '-')

        if is_crypto:
            ticker = ticker + '-USD'

        if is_future:
            ticker = ticker + '=F'

        if fill_digits:
            ticker = ticker.zfill(fill_digits)

        if exchange:
            ticker = f'{ticker}.{exchange}'

        tickers.append(ticker)

    return tickers


def get_s_p_500_tickers():
    source = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tickers = get_tickers(source, replace_dots=True)
    tickers.append('^GSPC')
    return tickers


def get_nasdaq_100_tickers():
    source = 'https://en.wikipedia.org/wiki/Nasdaq-100'
    column = 1
    tickers = get_tickers(source, column=column, replace_dots=True)
    tickers.append('^NDX')
    return tickers


def get_dow_jones_tickers():
    source = 'https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average'
    column = 1
    tickers = get_tickers(source, column=column, replace_dots=True)
    tickers.append('^DJI')
    print(list(reversed(tickers)))
    return tickers


def get_euro_stoxx_50_tickers():
    source = 'https://en.wikipedia.org/wiki/EURO_STOXX_50'
    tickers = get_tickers(source)
    tickers.append('^STOXX50E')
    return tickers


def get_dax_tickers():
    source = 'https://en.wikipedia.org/wiki/DAX'
    column = 3
    tickers = get_tickers(source, column=column)
    tickers.append('^GDAXI')
    return tickers


def get_mdax_tickers():
    source = 'https://en.wikipedia.org/wiki/MDAX'
    column = 7
    exchange = 'DE'
    tickers = get_tickers(source, column=column, exchange=exchange)
    tickers.append('^MDAXI')
    return tickers


def get_tecdax_tickers():
    source = 'https://de.wikipedia.org/wiki/TecDAX'
    id = 'zusammensetzung'
    column = 2
    exchange = 'DE'
    tickers = get_tickers(source, attribute='id', name=id, column=column, exchange=exchange)
    tickers.append('^TECDAX')
    print(list(reversed(tickers)))
    return tickers


def get_swiss_market_index():
    source = 'https://en.wikipedia.org/wiki/Swiss_Market_Index'
    attribute = 'class'
    name = 'wikitable'
    column = 3
    tickers = get_tickers(source, attribute=attribute, name=name, column=column)
    tickers.append('^SSMI')
    return tickers


def get_ftse_100_tickers():
    source = 'https://en.wikipedia.org/wiki/FTSE_100_Index'
    column = 1
    exchange = 'L'
    tickers = get_tickers(source, column=column, exchange=exchange)
    tickers.append('^FTSE')
    return tickers


def get_cac_40_tickers():
    source = 'https://en.wikipedia.org/wiki/CAC_40'
    column = 3
    tickers = get_tickers(source, column=column)
    tickers.append('^FCHI')
    print(list(reversed(tickers)))
    return tickers


def get_asx_50_tickers():
    source = 'https://en.wikipedia.org/wiki/S%26P/ASX_50'
    attribute = 'class'
    name = 'wikitable'
    exchange = 'AX'
    tickers = get_tickers(source, attribute=attribute, name=name, exchange=exchange)
    tickers.append('^AFLI')
    return tickers


def get_hang_seng_tickers():
    source = 'https://en.wikipedia.org/wiki/Hang_Seng_Index'
    exchange = 'HK'
    tickers = get_tickers(source, exchange=exchange, fill_digits=4)
    tickers.append('^HSI')
    return tickers


def get_nikkei_225_tickers():
    source = 'https://de.wikipedia.org/wiki/Nikkei_225'
    attribute = 'class'
    name = 'wikitable'
    table_index = -1
    column = 1
    exchange = 'T'
    tickers = get_tickers(source, attribute=attribute, name=name, table_index=table_index, column=column, exchange=exchange)
    tickers.append('^N225')
    return tickers


def get_kospi_tickers():
    source = 'https://en.wikipedia.org/wiki/KOSPI'
    attribute = 'class'
    name = 'wikitable'
    table_index = 3
    column = 2
    exchange = 'KS'
    tickers = get_tickers(source, attribute=attribute, name=name, table_index=table_index, column=column, exchange=exchange)
    tickers.append('^KS200')
    return tickers


def get_cryptocurrency_tickers():
    source = 'https://en.wikipedia.org/wiki/List_of_cryptocurrencies'
    attribute = 'class'
    name = 'wikitable'
    column = 2
    return get_tickers(source, attribute=attribute, name=name, column=column, is_crypto=True)


def get_precious_metals_tickers():
    source = 'https://en.wikipedia.org/wiki/List_of_traded_commodities'
    attribute = 'class'
    name = 'wikitable'
    table_index = 6
    column = 4
    return get_tickers(source, attribute=attribute, name=name, table_index=table_index, column=column, is_future=True)


def get_all_tickers():
    tickers = []
    tickers.extend(get_dax_tickers())  # Germany
    tickers.extend(get_nasdaq_100_tickers())  # United States
    tickers.extend(get_s_p_500_tickers())  # United States
    tickers.extend(get_dow_jones_tickers())  # United States
    tickers.extend(get_mdax_tickers())  # Germany
    tickers.extend(get_euro_stoxx_50_tickers())  # Europe
    tickers.extend(get_nikkei_225_tickers())  # Japan
    tickers.extend(get_tecdax_tickers())  # Germany
    tickers.extend(get_cac_40_tickers())  # France
    tickers.extend(get_ftse_100_tickers())  # United Kingdom
    # tickers.extend(get_swiss_market_index())  # Switzerland
    # tickers.extend(get_asx_50_tickers())  # Australia
    # tickers.extend(get_hang_seng_tickers())  # Hong Kong
    # tickers.extend(get_kospi_tickers())  # South Korea
    tickers.extend(get_cryptocurrency_tickers())  # Cryptocurrencies
    tickers.extend(get_precious_metals_tickers())  # Precious Metals
    return sorted(list(set(tickers)))


if __name__ == '__main__':
    tickers = get_all_tickers()
    print(tickers)
    print(len(tickers))
