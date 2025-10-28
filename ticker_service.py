import bs4 as bs
import re
import requests
import yfinance
from bs4 import BeautifulSoup


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
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(source, headers=headers)
    soup = bs.BeautifulSoup(resp.text, 'lxml')

    tables = soup.find_all('table', {attribute: name})
    if not tables:
        print(f'No tables found with {attribute}="{name}" on {source}')
        return []
    if table_index >= len(tables) or table_index < -len(tables):
        print(f'Table index {table_index} out of range for {source}')
        return []
    table = tables[table_index]

    tickers = []
    rows = table.find_all('tr')
    data_rows = [row for row in rows if row.find_all('td')]
    if not data_rows or len(data_rows[0].find_all('td')) <= column:
        print(f'Column {column} out of range in table for {source}')
        return []

    for row in data_rows:
        cells = row.find_all('td')
        if len(cells) <= column:
            continue
        ticker = cells[column].text.strip()
        ticker = ticker.split(',')[0].split('[')[0].split(':')[-1].strip()

        if not ticker:
            continue

        if replace_dots:
            ticker = ticker.replace('.', '-')

        if is_crypto:
            tickers.append(ticker + '-EUR')
            ticker = ticker + '-USD'

        if is_future:
            ticker = ticker + '=F'

        if fill_digits:
            ticker = ticker.zfill(fill_digits)

        if exchange:
            ticker = f'{ticker}.{exchange}'

        tickers.append(ticker)

    return list(set(tickers))


def get_s_p_500_tickers():
    source = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tickers = get_tickers(source, replace_dots=True)
    tickers.append('^GSPC')
    return tickers


def get_nasdaq_100_tickers():
    source = 'https://en.wikipedia.org/wiki/Nasdaq-100'
    tickers = get_tickers(source, replace_dots=True)
    tickers.append('^NDX')
    return tickers


def get_dow_jones_tickers():
    source = 'https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average'
    column = 1
    tickers = get_tickers(source, column=column, replace_dots=True)
    tickers.append('^DJI')
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
    tickers = [ticker.replace('ECV.DE', 'ECV.HM') for ticker in tickers]
    return tickers


def get_tecdax_tickers():
    source = 'https://de.wikipedia.org/wiki/TecDAX'
    name = 'zusammensetzung'
    column = 2
    exchange = 'DE'
    tickers = get_tickers(source, name=name, column=column, exchange=exchange)
    tickers.append('^TECDAX')
    return tickers


def get_smi_tickers():
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
    # source = 'https://de.wikipedia.org/wiki/Nikkei_225'
    # attribute = 'class'
    # name = 'wikitable'
    # table_index = -1
    # column = 1
    # exchange = 'T'
    # tickers = get_tickers(source, attribute=attribute, name=name, table_index=table_index, column=column, exchange=exchange)
    # # tickers.append('^N225')
    # return tickers

    headers = {'User-Agent': 'Mozilla/5.0'}
    source = 'https://en.wikipedia.org/wiki/Nikkei_225'
    response = requests.get(source, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all occurrences of "(TYO: " and extract the next four characters
    matches = re.findall(r'\(TYO: (\w{4})', soup.text)

    tickers = [f'{tyo}.T' for tyo in list(set(matches))]
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


def get_atx_tickers():
    source = 'https://www.wienerborse.at/en/index/atx-AT0000999982/composition/'
    resp = requests.get(source)
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    tables = soup.find_all('table', {'class': 'table-horizontal'})
    table = tables[1]
    tickers = []

    for row in table.findAll('tr')[1:]:
        cell = row.findAll('td')[0]
        isin = cell.findAll('span', {'class': 'isin'})[0].text.strip()

        if not isin:
            continue

        try:
            ticker = yfinance.Search(isin, max_results=1).all['quotes'][0]['symbol']
        except Exception as e:
            print(f'Error fetching ticker for ISIN {isin}: {e}')
            ticker = None

        if not ticker:
            continue

        tickers.append(ticker)

    tickers.append('^ATX')

    return tickers


def get_etf_tickers(index_ticker):
    if index_ticker == '^GSPC':
        return [
            "CSSPX.MI",
            "XS2D.L",
            "3USL.L",
        ]

    if index_ticker == "^NDX":
        return [
            "SXRV.DE",
            "LQQ.PA",
            "QQQ3.L",
        ]

    if index_ticker == "^GDAXI":
        return [
            "DBXD.DE",
            "DEL2.DE",
            "3DEL.L",
        ]

    if index_ticker == "BTC-USD":
        return [
            "BTC-USD",
            "BTC-USD",
            "BTC-USD",
        ]


def is_index(ticker):
    return ticker[0] == '^'


def is_crypto(ticker):
    return ticker[-4:] == '-USD' or ticker[-4:] == '-EUR'


def is_future(ticker):
    return ticker[-2:] == '=F'

def is_stock(ticker):
    return not is_index(ticker) and not is_crypto(ticker) and not is_future(ticker)


def get_hype_tickers():
    return [
        'RHM.DE',  # Rheinmetall AG
        'R3NK.DE',  # RENK Group AG
        'HAG.DE',  # Hensoldt AG
        'GC=F',  # Gold Futures
        'GME',  # GameStop Corp.
        'TSLA',  # Tesla, Inc.
        'NVDA',  # NVIDIA Corporation
        'AAPL',  # Apple Inc.
        'BTC-EUR',  # Bitcoin EUR Price
        'PLTR',  # Palantir Technologies Inc.
        'MSTR',  # Strategy Incorporated
        'HIMS',  # Hims & Hers Health, Inc.
        'DEZ.DE',  # DEUTZ Aktiengesellschaft
        'NVO',  # Novo Nordisk A/S
        '1211.HK',  # BYD COMPANY
        'DRO.AX',  # DroneShield Limited
        'PLTR',  # Palantir Technologies Inc.
        'ENR.DE',  # Siemens Energy AG
        '1810.HK',  # XIAOMI-W
        'QBTS',  # D-Wave Quantum Inc.
        'CLTE.NE',  # Clara Technologies Corp.
        'FLT.V',  # Volatus Aerospace Inc.
        'ASML',  # ASML Holding N.V.
        'OPEN',  # Opendoor Technologies Inc.
        '3350.T',  # Metaplanet Inc.
        'SAP.DE',  # SAP SE
        'PUM.DE',  # Puma SE
        'INTC',  # Intel Corporation
        'VOW3.DE',  # Volkswagen AG
        'MBG.DE',  # Mercedes-Benz Group AG
        'PYPL',  # PayPal Holdings, Inc.
        'HDD.F',  # Heidelberger Druckmaschinen Aktiengesellschaft
        'ADS.DE',  # Adidas AG
        'AMZN',  # Amazon.com, Inc.
        'FTNT',  # Fortinet, Inc.
        'CBK.DE',  # Commerzbank AG
        'NOK',  # Nokia Corporation
        'MRVL',  # Marvell Technology, Inc.
    ]

    
def get_all_tickers():
    tickers = []

    try:
        dax_tickers = get_dax_tickers()
        if len(dax_tickers) < 40:
            print('DAX tickers missing!')
        else:
            print(f'DAX tickers: {len(dax_tickers)}')
        tickers.extend(dax_tickers)  # Germany 40
    except Exception as e:
        print(f'Error fetching DAX tickers: {e}')

    try:
        nasdaq_100_tickers = get_nasdaq_100_tickers()
        if len(nasdaq_100_tickers) < 100:
            print('NASDAQ 100 tickers missing!')
        else:
            print(f'NASDAQ 100 tickers: {len(nasdaq_100_tickers)}')
        tickers.extend(nasdaq_100_tickers)  # United States 100
    except Exception as e:
        print(f'Error fetching NASDAQ 100 tickers: {e}')

    try:
        s_p_500_tickers = get_s_p_500_tickers()
        if len(s_p_500_tickers) < 500:
            print('S&P 500 tickers missing!')
        else:
            print(f'S&P 500 tickers: {len(s_p_500_tickers)}')
        tickers.extend(s_p_500_tickers)  # United States 500
    except Exception as e:
        print(f'Error fetching S&P 500 tickers: {e}')

    try:
        dow_jones_tickers = get_dow_jones_tickers()
        if len(dow_jones_tickers) < 30:
            print('Dow Jones tickers missing!')
        else:
            print(f'Dow Jones tickers: {len(dow_jones_tickers)}')
        tickers.extend(dow_jones_tickers)  # United States 30
    except Exception as e:
        print(f'Error fetching Dow Jones tickers: {e}')

    try:
        mdax_tickers = get_mdax_tickers()
        if len(mdax_tickers) < 50:
            print('MDAX tickers missing!')
        else:
            print(f'MDAX tickers: {len(mdax_tickers)}')
        tickers.extend(mdax_tickers)  # Germany 50
    except Exception as e:
        print(f'Error fetching MDAX tickers: {e}')

    try:
        euro_stoxx_50_tickers = get_euro_stoxx_50_tickers()
        if len(euro_stoxx_50_tickers) < 50:
            print('EURO STOXX 50 tickers missing!')
        else:
            print(f'EURO STOXX 50 tickers: {len(euro_stoxx_50_tickers)}')
        tickers.extend(euro_stoxx_50_tickers)  # Europe 50
    except Exception as e:
        print(f'Error fetching EURO STOXX 50 tickers: {e}')

    try:
        nikkei_225_tickers = get_nikkei_225_tickers()
        if len(nikkei_225_tickers) < 225:
            print('Nikkei 225 tickers missing!')
        else:
            print(f'Nikkei 225 tickers: {len(nikkei_225_tickers)}')
        tickers.extend(nikkei_225_tickers)  # Japan 225
    except Exception as e:
        print(f'Error fetching Nikkei 225 tickers: {e}')

    try:
        tecdax_tickers = get_tecdax_tickers()
        if len(tecdax_tickers) < 30:
            print('TecDAX tickers missing!')
        else:
            print(f'TecDAX tickers: {len(tecdax_tickers)}')
        tickers.extend(tecdax_tickers)  # Germany 30
    except Exception as e:
        print(f'Error fetching TecDAX tickers: {e}')

    try:
        cac_40_tickers = get_cac_40_tickers()
        if len(cac_40_tickers) < 40:
            print('CAC 40 tickers missing!')
        else:
            print(f'CAC 40 tickers: {len(cac_40_tickers)}')
        tickers.extend(cac_40_tickers)  # France 40
    except Exception as e:
        print(f'Error fetching CAC 40 tickers: {e}')

    try:
        ftse_100_tickers = get_ftse_100_tickers()
        if len(ftse_100_tickers) < 100:
            print('FTSE 100 tickers missing!')
        else:
            print(f'FTSE 100 tickers: {len(ftse_100_tickers)}')
        tickers.extend(ftse_100_tickers)  # United Kingdom 100
    except Exception as e:
        print(f'Error fetching FTSE 100 tickers: {e}')

    try:
        smi_tickers = get_smi_tickers()
        if len(smi_tickers) < 20:
            print('SMI tickers missing!')
        else:
            print(f'SMI tickers: {len(smi_tickers)}')
        tickers.extend(smi_tickers)  # Switzerland 20
    except Exception as e:
        print(f'Error fetching SMI tickers: {e}')

    try:
        atx_tickers = get_atx_tickers()
        if len(atx_tickers) < 20:
            print('ATX tickers missing!')
        else:
            print(f'ATX tickers: {len(atx_tickers)}')
        tickers.extend(atx_tickers)  # Austria 20
    except Exception as e:
        print(f'Error fetching ATX tickers: {e}')

    try:
        cryptocurrency_tickers = get_cryptocurrency_tickers()
        print(f'Cryptocurrency tickers: {len(cryptocurrency_tickers)}')
        tickers.extend(cryptocurrency_tickers)
    except Exception as e:
        print(f'Error fetching cryptocurrency tickers: {e}')

    try:
        precious_metals_tickers = get_precious_metals_tickers()
        print(f'Precious metals tickers: {len(precious_metals_tickers)}')
        tickers.extend(precious_metals_tickers)
    except Exception as e:
        print(f'Error fetching precious metals tickers: {e}')

    try:
        hype_tickers = get_hype_tickers()
        print(f'Hype tickers: {len(hype_tickers)}')
        tickers.extend(hype_tickers)
    except Exception as e:
        print(f'Error fetching hype tickers: {e}')

    # tickers.extend(get_asx_50_tickers())  # Australia
    # tickers.extend(get_hang_seng_tickers())  # Hong Kong
    # tickers.extend(get_kospi_tickers())  # South Korea
    # tickers.extend(get_cryptocurrency_tickers())  # Cryptocurrencies
    # tickers.extend(get_precious_metals_tickers())  # Precious Metals
    return sorted(list(set(tickers)))


if __name__ == '__main__':
    # main_tickers = get_all_tickers()
    # print(len(main_tickers))
    print(get_dax_tickers())