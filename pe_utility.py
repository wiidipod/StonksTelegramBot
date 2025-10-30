import requests
from bs4 import BeautifulSoup

def get_pe_ratios():
    url = "https://fullratio.com/pe-ratio-by-industry"

    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table', class_='metric-by-industry')

        if not table:
            return {}

        pe_ratios = {}

        rows = table.find_all('tr')[1:]

        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                industry = cols[0].text.strip()
                pe_ratio = float(cols[1].text.strip())
                pe_ratios[industry] = pe_ratio

        return pe_ratios
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return {}
    except Exception as e:
        print(f"Error parsing data: {e}")
        return {}

if __name__ == "__main__":
    pe_ratios = get_pe_ratios()
    for industry, ratio in pe_ratios.items():
        print(f"{industry}: {ratio}")
