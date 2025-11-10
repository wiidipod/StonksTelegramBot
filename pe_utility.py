from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


def get_pe_ratios():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://fullratio.com/pe-ratio-by-industry")

        # Wait for table to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "metric-by-industry"))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        table = soup.find('table', class_='metric-by-industry')

        if not table:
            return {}

        pe_ratios = {}
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

        return pe_ratios
    except Exception as e:
        print(f"Error: {e}")
        return {}


if __name__ == "__main__":
    pe_ratios = get_pe_ratios()
    for industry, ratio in pe_ratios.items():
        print(f"{industry}: {ratio}")