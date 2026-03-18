import bs4 as bs
import re
import requests
import yfinance
from bs4 import BeautifulSoup


def chunk_list(lst, chunk_size):
    for list_index in range(0, len(lst), chunk_size):
        yield lst[list_index:list_index + chunk_size]


def get_tickers(
        source,
        attribute='id',
        name='constituents',
        table_index=0,
        column=0,
        replace_dots=False,
        replace_space=False,
        exchange=None,
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

    # Normalize exchange into a list for consistent iteration
    if isinstance(exchange, str) and exchange:
        exchange_list = [exchange]
    elif isinstance(exchange, list):
        exchange_list = exchange
    else:
        exchange_list = []

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
        if replace_space:
            ticker = ticker.replace(' ', '-')
        ticker = ticker.split(',')[0].split('[')[0].split(':')[-1].strip().split(' ')[0].strip()

        if not ticker:
            continue

        if replace_dots:
            ticker = ticker.replace('.', '-')

        if is_crypto:
            tickers.append(f'{ticker}-USD')
            tickers.append(f'{ticker}-EUR')
            continue

        if is_future:
            tickers.append(f'{ticker}=F')
            continue

        if fill_digits:
            ticker = ticker.zfill(fill_digits)

        # Handle exchange logic
        if exchange_list:
            for e in exchange_list:
                tickers.append(f'{ticker}.{e}')
        else:
            tickers.append(ticker)

    return list(set(tickers))


def get_s_p_500_tickers():
    source = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tickers = get_tickers(source, replace_dots=True)
    tickers.append('^GSPC')
    return tickers


def get_s_p_400_tickers():
    source = 'https://en.wikipedia.org/wiki/List_of_S%26P_400_companies'
    tickers = get_tickers(source, replace_dots=True)
    tickers.append('^SP400')
    return tickers


def get_s_p_600_tickers():
    source = 'https://en.wikipedia.org/wiki/List_of_S%26P_600_companies'
    tickers = get_tickers(source, replace_dots=True)
    tickers.append('^SP600')
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
    tickers = get_tickers(source)
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


def get_sse_50_tickers():
    source = 'https://en.wikipedia.org/wiki/SSE_50_Index'
    exchange = 'SS'
    tickers = get_tickers(source, column=1, exchange=exchange, fill_digits=6)
    tickers.append('000016.SS')
    return tickers


def get_ibovespa_tickers():
    source = 'https://en.wikipedia.org/wiki/List_of_companies_listed_on_B3'
    column = 1
    exchange = 'SA'
    tickers = get_tickers(source, column=column, exchange=exchange)
    tickers.append('^BVSP')
    return tickers


def get_nifty_50_tickers():
    source = 'https://en.wikipedia.org/wiki/NIFTY_50'
    column = 1
    exchanges = ['NS', 'BO']
    tickers = get_tickers(source, column=column, exchange=exchanges)
    tickers.append('^NSEI')
    return tickers


def get_ftse_250_tickers():
    source = 'https://en.wikipedia.org/wiki/FTSE_250_Index'
    column = 1
    exchange = 'L'
    tickers = get_tickers(source, column=column, exchange=exchange)
    tickers.append('^FTMC')
    return tickers


def get_tsx_60_tickers():
    source = 'https://en.wikipedia.org/wiki/S%26P/TSX_60'
    exchange = 'TO'
    attribute = 'class'
    name = 'wikitable'
    tickers = get_tickers(source, attribute=attribute, name=name, exchange=exchange, replace_dots=True)
    tickers.append('TX60.TS')
    return tickers


def get_tsx_composite_tickers():
    source = 'https://en.wikipedia.org/wiki/S%26P/TSX_Composite_Index'
    name = 'components'
    exchange = 'TO'
    tickers = get_tickers(source, name=name, exchange=exchange, replace_dots=True)
    tickers.append('^GSPTSE')
    return tickers


def get_omx_stockholm_30_tickers():
    source = 'https://en.wikipedia.org/wiki/OMX_Stockholm_30'
    attribute = 'class'
    name = 'wikitable'
    tickers = get_tickers(source, attribute=attribute, name=name)
    tickers.append('^OMX')
    return tickers


def get_omx_copenhagen_25_tickers():
    source = 'https://en.wikipedia.org/wiki/OMX_Copenhagen_25'
    attribute = 'class'
    name = 'wikitable'
    column = 2
    exchange = 'CO'
    tickers = get_tickers(source, attribute=attribute, name=name, column=column, exchange=exchange, replace_space=True)
    tickers.append('^OMXC25')
    return tickers


def get_ibex_35_tickers():
    source = 'https://en.wikipedia.org/wiki/IBEX_35'
    name = 'components'
    tickers = get_tickers(source, name=name)
    tickers.append('^IBEX')
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


def get_energy_tickers():
    source = 'https://en.wikipedia.org/wiki/List_of_traded_commodities'
    attribute = 'class'
    name = 'wikitable'
    table_index = 3
    column = 3
    tickers = get_tickers(source, attribute=attribute, name=name, table_index=table_index, column=column, is_future=True)
    return tickers
    # tickers = [ticker.split(' ') for ticker in tickers]
    # return [ticker for ticker in tickers if '(' not in ticker]


def get_atx_tickers():
    source = 'https://www.wienerborse.at/en/index/atx-AT0000999982/composition/'
    resp = requests.get(source)
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    tables = soup.find_all('table', {'class': 'table-horizontal'})
    table = tables[1]
    tickers = []

    for row in table.find_all('tr')[1:]:
        cell = row.find_all('td')[0]
        isin = cell.find_all('span', {'class': 'isin'})[0].text.strip()

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


def get_currency_tickers():
    return [
        "EUR=X",

        # Major Currency Pairs
        'EURUSD=X',  # EUR/USD
        'JPY=X',     # USD/JPY
        'GBPUSD=X',  # GBP/USD
        'AUDUSD=X',  # AUD/USD
        'NZDUSD=X',  # NZD/USD

        # Cross Currency Pairs
        'EURJPY=X',  # EUR/JPY
        'GBPJPY=X',  # GBP/JPY
        'EURGBP=X',  # EUR/GBP
        'EURCAD=X',  # EUR/CAD
        'EURSEK=X',  # EUR/SEK
        'EURCHF=X',  # EUR/CHF
        'EURHUF=X',  # EUR/HUF

        # Asian Currencies
        'CNY=X',     # USD/CNY
        'HKD=X',     # USD/HKD
        'SGD=X',     # USD/SGD
        'INR=X',     # USD/INR
        'PHP=X',     # USD/PHP
        'IDR=X',     # USD/IDR
        'THB=X',     # USD/THB
        'MYR=X',     # USD/MYR

        # Emerging Markets
        'MXN=X',     # USD/MXN
        'ZAR=X',     # USD/ZAR
        'RUB=X',     # USD/RUB
    ]


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


exchange_codes = {
    "NASDAQ": "",
    "New York Stock Exchange Inc.": "",
    "Toronto Stock Exchange": ".TO",
    "London Stock Exchange": ".L",
    "Euronext Amsterdam": ".AS",
    "Xetra": ".DE",
    "SIX Swiss Exchange": ".SW",
    "Tokyo Stock Exchange": ".T",
    "Hong Kong Exchanges And Clearing Ltd": ".HK",
    "Asx - All Markets": ".AX",
    "Nyse Euronext - Euronext Paris": ".PA",
    "Bolsa De Madrid": ".MC",
    "Borsa Italiana": ".MI",
    "Omx Nordic Exchange Copenhagen A/S": ".CO",
    "Singapore Exchange": ".SI",
    "Nasdaq Omx Nordic": ".ST",
    "Nasdaq Omx Helsinki Ltd.": ".HE",
    "Oslo Bors Asa": ".OL",
    "Nyse Euronext - Euronext Brussels": ".BR",
    "Irish Stock Exchange - All Market": ".IR",
    "Wiener Boerse Ag": ".VI",
    "Tel Aviv Stock Exchange": ".TA",
    "New Zealand Exchange Ltd": ".NZ",
    "Nyse Euronext - Euronext Lisbon": ".LS",
    "Cboe BZX": "",
}


replacemenet_tickers = {
    "2299955D.TO": "CSU.TO",
    "BFB": "BF-B",
    "BRKB": "BRK-B",
    "HEIA": "HEIA.AS",
    "FI": "FISV",
}


def get_msci_world_tickers():
    import csv
    import os

    tickers = []
    missing_exchanges = {}  # Changed to dict to track tickers per exchange

    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # https://www.ishares.com/de/privatanleger/de/produkte/251882/ishares-msci-world-ucits-etf-acc-fund/1478358465952.ajax?fileType=csv&fileName=EUNL_holdings&dataType=fund
    csv_path = os.path.join(script_dir, 'EUNL_holdings.csv')

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            # Skip the first 3 rows (headers)
            if i < 3:
                continue

            # Make sure we have enough columns
            if len(row) < 11:
                continue

            ticker = row[0].strip()
            exchange = row[10].strip()

            # Skip cash and derivatives
            if not ticker or exchange == '-':
                continue

            # Replace spaces with dashes in ticker
            ticker = ticker.replace(' ', '-')

            # Strip trailing dots (common in UK stocks in data sources)
            ticker = ticker.rstrip('.')

            # Replace dots with dashes if needed
            ticker = ticker.replace(".", "-")

            # Pad Hong Kong tickers with leading zeros to 4 digits
            if exchange == "Hong Kong Exchanges And Clearing Ltd":
                # Check if ticker is all digits
                if ticker.isdigit():
                    ticker = ticker.zfill(4)

            # Get the country code based on exchange
            if exchange in exchange_codes:
                country_code = exchange_codes[exchange]
                ticker = ticker + country_code
            else:
                # Track missing exchanges and their tickers
                if exchange not in missing_exchanges:
                    missing_exchanges[exchange] = []
                missing_exchanges[exchange].append(ticker)
                # Still add the ticker without suffix

            if ticker in replacemenet_tickers:
                ticker = replacemenet_tickers[ticker]

            tickers.append(ticker)

    # Print any missing exchanges with their tickers
    if missing_exchanges:
        print("Missing exchanges in exchange_codes:")
        for exchange in sorted(missing_exchanges.keys()):
            tickers_list = ', '.join(missing_exchanges[exchange])
            print(f"  - {exchange}")
            print(f"    Tickers: {tickers_list}")

    return tickers


def get_index_tickers():
    return [
        '^GSPC',      # S&P 500
        '^DJI',       # Dow Jones Industrial Average
        '^IXIC',      # NASDAQ Composite
        '^NYA',       # NYSE Composite Index
        '^XAX',       # NYSE American Composite Index
        '^BUK100P',   # Cboe UK 100
        '^RUT',       # Russell 2000 Index
        '^VIX',       # CBOE Volatility Index
        '^FTSE',      # FTSE 100
        '^GDAXI',     # DAX P
        '^FCHI',      # CAC 40
        '^STOXX50E',  # EURO STOXX 50 I
        '^N100',      # Euronext 100 Index
        '^BFX',       # BEL 20
        '^HSI',       # HANG SENG INDEX
        '^STI',       # STI Index
        '^AXJO',      # S&P/ASX 200
        '^AORD',      # ALL ORDINARIES
        '^BSESN',     # S&P BSE SENSEX
        '^JKSE',      # IDX COMPOSITE
        '^KLSE',      # FTSE Bursa Malaysia KLCI
        '^NZ50',      # S&P/NZX 50 INDEX GROSS
        '^KS11',      # KOSPI Composite Index
        '^TWII',      # TWSE Capitalization Weighted Stock Index
        '^GSPTSE',    # S&P/TSX Composite index
        '^BVSP',      # IBOVESPA
        '^MXX',       # IPC MEXICO
        '^IPSA',      # S&P IPSA
        '^MERV',      # MERVAL
        '^TA125.TA',  # TA-125
        '^CASE30',    # EGX 30 Price Return Index
        '^JN0U.JO',   # Top 40 USD Net TRI Index
        '000001.SS',  # SSE Composite Index
        '000016.SS',  # SSE 50 Index
        '^N225',      # Nikkei 225
        'MOEX.ME',    # Moscow Exchange MICEX-RTS
        'DX-Y.NYB',   # US Dollar Index
        '^125904-USD-STRD',  # MSCI EUROPE
        '^XDB',       # British Pound Currency Index
        '^XDE',       # Euro Currency Index
        '^XDN',       # Japanese Yen Currency Index
        '^XDA',       # Australian Dollar Currency Index
        '^SDAXI',     # SDAX P
        '^SSHI',      # SPI TR
        '^NSEI',       # Nifty 50
        '^FTMC',       # FTSE 250
        'TX60.TS',       # S&P/TSX 60
        '^OMX',        # OMX Stockholm 30
        '^OMXC25',     # OMX Copenhagen 25
        '^IBEX',        # IBEX 35
        '^KS200',       # KOSPI 200
        '^AFLI',        # S&P/ASX 50
        '^SSMI',       # SMI Index
        '^TECDAX',      # TecDAX
        '^MDAXI',       # MDAX P
        '^STOXX50E',      # EURO STOXX 50 I
        '^NDX',        # NASDAQ 100
        '^SP600',       # S&P 600
        '^SP400',       # S&P 400
    ]


def get_future_tickers():
    return [
        # Equity Index Futures
        'ES=F',   # E-Mini S&P 500
        'YM=F',   # Mini Dow Jones Industrial
        'NQ=F',   # Nasdaq 100
        'RTY=F',  # E-mini Russell 2000

        # Treasury Futures
        'ZB=F',   # U.S. Treasury Bond
        'ZN=F',   # 10-Year T-Note
        'ZF=F',   # 5-Year T-Note
        'ZT=F',   # 2-Year T-Note
        '2YY=F',  # 2-Year Yield Futures

        # Metals Futures
        'GC=F',   # Gold
        'MGC=F',  # Micro Gold
        'SI=F',   # Silver
        'SIL=F',  # Micro Silver
        'PL=F',   # Platinum
        'HG=F',   # Copper
        'PA=F',   # Palladium

        # Energy Futures
        'CL=F',   # Crude Oil
        'HO=F',   # Heating Oil
        'NG=F',   # Natural Gas
        'RB=F',   # RBOB Gasoline
        'BZ=F',   # Brent Crude Oil
        'B0=F',   # Mont Belvieu LDH Propane

        # Agricultural Futures - Grains
        'ZC=F',   # Corn
        'ZO=F',   # Oat
        'KE=F',   # KC HRW Wheat
        'ZR=F',   # Rough Rice
        'ZM=F',   # Soybean Meal
        'ZL=F',   # Soybean Oil
        'ZS=F',   # Soybean

        # Agricultural Futures - Livestock
        'GF=F',   # Feeder Cattle
        'HE=F',   # Lean Hog
        'LE=F',   # Live Cattle

        # Agricultural Futures - Softs
        'CC=F',   # Cocoa
        'KC=F',   # Coffee
        'CT=F',   # Cotton
        'LBS=F',  # Random Length Lumber
        'OJ=F',   # Orange Juice
        'SB=F',   # Sugar #11
    ]


def get_bond_tickers():
    return [
        '^IRX',   # 13 Week Treasury Bill
        '^FVX',   # Treasury Yield 5 Years
        '^TNX',   # CBOE Interest Rate 10 Year T No
        '^TYX',   # Treasury Yield 30 Years
        '2YY=F',  # 2-Year Yield Futures
        'ZN=F',   # 10-Year T-Note Futures
    ]


def get_3x_etf_tickers():
    return [
        '3OIL.L',  # WTI Crude Oil
        '3OIS.L',  # WTI Crude Oil Short
        '3BRL.L',  # Brent Crude Oil
        '3BRS.L',  # Brent Crude Oil Short
        '3SIL.L',  # Silver
        '3SIS.L',  # Silver Short
        'QQQ3.L',  # NASDAQ 100
        'QQQS.L',  # NASDAQ 100 Short
        '3LNG.L',  # Natural Gas
        '3NGS.L',  # Natural Gas Short
        '3GOL.L',  # Gold
        '3GOS.L',  # Gold Short
        '3LDE.L',  # DAX
        '3SDE.L',  # DAX Short
        '3BAL.L',  # EURO STOXX Banks
        '3BAS.MI',  # EURO STOXX Banks Short
        '3USL.L',  # S&P 500
        '3USS.L',  # S&P 500 Short
        '3EUL.L',  # EURO STOXX 50
        '3LES.L',  # EURO STOXX 50 Short
        '3SMC.L',  # Semiconductor
        'SC3S.L',  # Semiconductor Short
        '3EML.MI',  # Emerging Markets
        '3EMS.MI',  # Emerging Markets Short
        '3EDF.L',  # STOXX Europe Aerospa
        '3EDS.L',  # STOXX Europe Aerospa Short
        '3CAC.PA',  # CAC 40
        '3CAS.PA',  # CAC 40 Short
        '3HCL.L',  # Copper
        '3MG7.L',  # Magnificent 7
        '3M7S.L',  # Magnificent 7 Short
        '3TYL.MI',  # US Treasuries 10Y
        '3TYS.MI',  # US Treasuries 10Y Short
        '3UBS.MI',  # Bund 30Y Short
    ]


def is_index(ticker):
    return (ticker[0] == '^' and not is_bond(ticker)) or ticker in get_index_tickers()


def is_crypto(ticker):
    return ticker[-4:] == '-USD' or ticker[-4:] == '-EUR'


def is_future(ticker):
    return (ticker[-2:] == '=F' and not is_bond(ticker)) or ticker in get_future_tickers()


def is_currency(ticker):
    return ticker[-2:] == '=X' or ticker in get_currency_tickers()


def is_3x_etf(ticker):
    return ticker in get_3x_etf_tickers()


def is_bond(ticker):
    return ticker in get_bond_tickers()


def is_stock(ticker):
    return not is_index(ticker) and not is_crypto(ticker) and not is_future(ticker) and not is_currency(ticker) and not is_3x_etf(ticker) and not is_bond(ticker)


def sort_tickers(tickers):
    stock_tickers = sorted([t for t in tickers if is_stock(t)])
    index_tickers = sorted([t for t in tickers if is_index(t)])
    etf_tickers = sorted([t for t in tickers if is_3x_etf(t)])
    future_tickers = sorted([t for t in tickers if is_future(t)])
    currency_tickers = sorted([t for t in tickers if is_currency(t)])
    crypto_tickers = sorted([t for t in tickers if is_crypto(t)])
    bond_tickers = sorted([t for t in tickers if is_bond(t)])
    return stock_tickers + index_tickers + etf_tickers + future_tickers + currency_tickers + crypto_tickers + bond_tickers

    
def get_all_tickers():
    tickers = []

    try:
        msci_world_tickers = get_msci_world_tickers()
        if len(msci_world_tickers) < 1000:
            print('MSCI World tickers missing!')
        else:
            print(f'MSCI World tickers: {len(msci_world_tickers)}')
        tickers.extend(msci_world_tickers)  # MSCI World
    except Exception as e:
        print(f'Error fetching MSCI World tickers: {e}')

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
        s_p_400_tickers = get_s_p_400_tickers()
        if len(s_p_400_tickers) < 400:
            print('S&P 400 tickers missing!')
        else:
            print(f'S&P 400 tickers: {len(s_p_400_tickers)}')
        tickers.extend(s_p_400_tickers)  # United States 400
    except Exception as e:
        print(f'Error fetching S&P 400 tickers: {e}')

    try:
        s_p_600_tickers = get_s_p_600_tickers()
        if len(s_p_600_tickers) < 600:
            print('S&P 600 tickers missing!')
        else:
            print(f'S&P 600 tickers: {len(s_p_600_tickers)}')
        tickers.extend(s_p_600_tickers)  # United States 600
    except Exception as e:
        print(f'Error fetching S&P 600 tickers: {e}')

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
    tickers.extend([
        "BTC-EUR", "ETH-EUR", "XRP-EUR", "SOL-EUR", "ADA-EUR", "DOGE-EUR",
        "BTC-USD", "ETH-USD", "XRP-USD", "SOL-USD", "ADA-USD", "DOGE-USD",
    ])

    try:
        precious_metals_tickers = get_precious_metals_tickers()
        if len(precious_metals_tickers) != 4:
            print('Precious metals tickers missing!')
        else:
            print(f'Precious metals tickers: {len(precious_metals_tickers)}')
        tickers.extend(precious_metals_tickers) # Precious Metals
    except Exception as e:
        print(f'Error fetching precious metals tickers: {e}')
    tickers.extend(['GC=F', 'SI=F'])  # Precious Metals

    try:
        energy_tickers = get_energy_tickers()
        if len(energy_tickers) != 10:
            print('Energy tickers missing!')
        else:
            print(f'Energy tickers: {len(energy_tickers)}')
        tickers.extend(energy_tickers) # Energy
    except Exception as e:
        print(f'Error fetching energy tickers: {e}')
    tickers.extend(['BZ=F', 'CL=F'])  # Energy

    # tickers.extend(get_currency_tickers())  # Currencies

    tickers.extend(get_index_tickers())  # Additional Indexes

    tickers.extend(get_future_tickers())  # Futures

    tickers.extend(get_bond_tickers())  # Bonds

    tickers.extend(get_3x_etf_tickers())  # 3x ETFs

    # try:
    #     hype_tickers = get_hype_tickers()
    #     print(f'Hype tickers: {len(hype_tickers)}')
    #     tickers.extend(hype_tickers)
    # except Exception as e:
    #     print(f'Error fetching hype tickers: {e}')

    try:
        asx_50_tickers = get_asx_50_tickers()  # Australia
        if len(asx_50_tickers) < 50:
            print('ASX 50 tickers missing!')
        else:
            print(f'ASX 50 tickers: {len(asx_50_tickers)}')
        tickers.extend(asx_50_tickers)
    except Exception as e:
        print(f'Error fetching ASX 50 tickers: {e}')

    try:
        hang_seng_tickers = get_hang_seng_tickers()  # Hong Kong
        if len(hang_seng_tickers) < 80:
            print('Hang Seng tickers missing!')
        else:
            print(f'Hang Seng tickers: {len(hang_seng_tickers)}')
        tickers.extend(hang_seng_tickers)
    except Exception as e:
        print(f'Error fetching Hang Seng tickers: {e}')

    try:
        sse_50_tickers = get_sse_50_tickers()  # Shanghai
        if len(sse_50_tickers) < 50:
            print('SSE 50 tickers missing!')
        else:
            print(f'SSE 50 tickers: {len(sse_50_tickers)}')
        tickers.extend(sse_50_tickers)
    except Exception as e:
        print(f'Error fetching SSE 50 tickers: {e}')

    try:
        ibovespa_tickers = get_ibovespa_tickers()  # Brazil
        if len(ibovespa_tickers) < 80:
            print('Ibovespa tickers missing!')
        else:
            print(f'Ibovespa tickers: {len(ibovespa_tickers)}')
        tickers.extend(ibovespa_tickers)
    except Exception as e:
        print(f'Error fetching Ibovespa tickers: {e}')

    try:
        nifty_50_tickers = get_nifty_50_tickers()  # India
        if len(nifty_50_tickers) < 100:
            print('NIFTY 50 tickers missing!')
        else:
            print(f'NIFTY 50 tickers: {len(nifty_50_tickers)}')
        tickers.extend(nifty_50_tickers)
    except Exception as e:
        print(f'Error fetching NIFTY 50 tickers: {e}')

    try:
        ftse_250_tickers = get_ftse_250_tickers()  # Great Britain 250
        if len(ftse_250_tickers) < 250:
            print('FTSE 250 tickers missing!')
        else:
            print(f'FTSE 250 tickers: {len(ftse_250_tickers)}')
        tickers.extend(ftse_250_tickers)
    except Exception as e:
        print(f'Error fetching FTSE 250 tickers: {e}')

    try:
        tsx_60_tickers = get_tsx_60_tickers()  # Canada 60
        if len(tsx_60_tickers) < 60:
            print('S&P/TSX 60 tickers missing!')
        else:
            print(f'S&P/TSX 60 tickers: {len(tsx_60_tickers)}')
        tickers.extend(tsx_60_tickers)
    except Exception as e:
        print(f'Error fetching S&P/TSX 60 tickers: {e}')

    try:
        tsx_composite_tickers = get_tsx_composite_tickers()  # Canada
        if len(tsx_composite_tickers) < 200:
            print('S&P/TSX Composite tickers missing!')
        else:
            print(f'S&P/TSX Composite tickers: {len(tsx_composite_tickers)}')
        tickers.extend(tsx_composite_tickers)
    except Exception as e:
        print(f'Error fetching S&P/TSX Composite tickers: {e}')

    try:
        omx_stockholm_30_tickers = get_omx_stockholm_30_tickers()  # Stockholm 30
        if len(omx_stockholm_30_tickers) < 30:
            print('OMX Stockholm 30 tickers missing!')
        else:
            print(f'OMX Stockholm 30 tickers: {len(omx_stockholm_30_tickers)}')
        tickers.extend(omx_stockholm_30_tickers)
    except Exception as e:
        print(f'Error fetching OMX Stockholm 30 tickers: {e}')

    try:
        omx_copenhagen_25_tickers = get_omx_copenhagen_25_tickers()  # Copenhagen 25
        if len(omx_copenhagen_25_tickers) < 25:
            print('OMX Copenhagen 25 tickers missing!')
        else:
            print(f'OMX Copenhagen 25 tickers: {len(omx_copenhagen_25_tickers)}')
        tickers.extend(omx_copenhagen_25_tickers)
    except Exception as e:
        print(f'Error fetching OMX Copenhagen 25 tickers: {e}')

    try:
        ibex_35_tickers = get_ibex_35_tickers()  # Spain 35
        if len(ibex_35_tickers) < 35:
            print('IBEX 35 tickers missing!')
        else:
            print(f'IBEX 35 tickers: {len(ibex_35_tickers)}')
        tickers.extend(ibex_35_tickers)
    except Exception as e:
        print(f'Error fetching IBEX 35 tickers: {e}')

    tickers = sort_tickers(list(set(tickers)))
    print(f"Total tickers collected: {len(tickers)}")
    return tickers
    # return tickers


if __name__ == '__main__':
    # print(get_energy_tickers())
    # print(get_precious_metals_tickers())
    # print(get_cryptocurrency_tickers())

    main_tickers = get_all_tickers()
    print(len(main_tickers))
    # print(main_tickers)
