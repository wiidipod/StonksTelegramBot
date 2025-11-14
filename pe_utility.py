from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import os


def update_pe_ratios(csv_file='pe_ratios.csv'):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    try:
        driver = webdriver.Chrome(options=chrome_options)

        # Get industry PE ratios
        driver.get("https://fullratio.com/pe-ratio-by-industry")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "metric-by-industry"))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table', class_='metric-by-industry')

        pe_ratios = {}
        if table:
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    industry = cols[0].text.strip()
                    try:
                        pe_ratio = float(cols[1].text.strip())
                        pe_ratios[industry] = pe_ratio
                    except ValueError:
                        continue

        # Get S&P 500 PE ratio
        driver.get("https://www.multpl.com/s-p-500-pe-ratio/table/by-year")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "tbody"))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tbody = soup.find('tbody')

        if tbody:
            rows = tbody.find_all('tr')
            if len(rows) > 1:
                first_data_row = rows[1]
                cols = first_data_row.find_all('td')
                if len(cols) >= 2:
                    try:
                        sp500_pe = float(cols[1].text.strip().replace('†', '').strip())
                        pe_ratios['S&P 500'] = sp500_pe
                    except ValueError:
                        pass

        driver.quit()

        # Save to CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Industry', 'PE_Ratio'])
            for industry, ratio in pe_ratios.items():
                writer.writerow([industry, ratio])

        return pe_ratios

    except Exception as e:
        print(f"Error: {e}")
        return {}


def get_pe_ratios(csv_file='pe_ratios.csv'):
    """Read PE ratios from CSV file, fallback to scraping if file doesn't exist."""
    if os.path.exists(csv_file):
        try:
            pe_ratios = {}
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pe_ratios[row['Industry']] = float(row['PE_Ratio'])
            return pe_ratios
        except Exception as e:
            print(f"Error reading CSV: {e}. Fetching fresh data...")
            return update_pe_ratios(csv_file)
    else:
        print("CSV file not found. Fetching fresh data...")
        return update_pe_ratios(csv_file)


if __name__ == "__main__":
    pe_ratios = update_pe_ratios()
    for industry, ratio in pe_ratios.items():
        print(f"{industry}: {ratio}")
    pe_ratios = get_pe_ratios()
    for industry, ratio in pe_ratios.items():
        print(f"{industry}: {ratio}")
