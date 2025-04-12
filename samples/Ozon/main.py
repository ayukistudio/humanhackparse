import requests
from bs4 import BeautifulSoup
from stopwatch import Stopwatch
from url import Url

TEST_PRODUCT_URL = Url('https://www.ozon.ru/product/976734881')

cookies = {}

headers = {
    'User-Agent': 'curl/8.8.0',
    'Accept': '*/*'
}

def _get_data_product(url: Url) -> tuple:
    if not isinstance(url, Url):
        raise ValueError('URL is invalid.')

    try:
        response = requests.get(url.full_url, headers=headers, allow_redirects=True)
        response.raise_for_status()  # Raise an error for bad status codes
    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch URL: {e}")

    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find elements with error handling
    name_shop = soup.find('a', class_='kv2_27')
    category = soup.find('ol', class_='je1_10')
    green_price = soup.find('span', class_='s5m_27 ms4_27')
    main_price = soup.find('span', class_='mt0_27 m0t_27 mt4_27')
    red_price = soup.find('span', class_='mt_27 tm0_27 ms9_27 tm_27')

    # Check for missing elements
    missing_elements = []
    if name_shop is None:
        missing_elements.append("name_shop (class kv2_27)")
    if category is None:
        missing_elements.append("category (class je1_10)")
    if green_price is None:
        missing_elements.append("green_price (class s5m_27 ms4_27)")
    if main_price is None:
        missing_elements.append("main_price (class mt0_27 m0t_27 mt4_27)")
    if red_price is None:
        missing_elements.append("red_price (class mt_27 tm0_27 ms9_27 tm_27)")

    if missing_elements:
        raise AttributeError(f"Missing elements: {', '.join(missing_elements)}")

    # Extract and clean data
    try:
        green_price_value = float(green_price.text.strip().replace('\xa0', '')[:-2])
        main_price_value = float(main_price.text.strip().replace('\xa0', '')[:-2])
        red_price_value = float(red_price.text.strip().replace('\xa0', '')[:-2])
    except (ValueError, TypeError) as e:
        raise ValueError(f"Failed to parse prices: {e}")

    return (
        name_shop.text.strip(),
        url.join(name_shop.get("href")),
        green_price_value,
        main_price_value,
        red_price_value
    )

def get_price_product(url: Url) -> tuple[float, float, float]:
    data = _get_data_product(url)
    return data[2], data[3], data[4]

if __name__ == '__main__':
    watch = Stopwatch()

    watch.start()
    try:
        d = _get_data_product(TEST_PRODUCT_URL)
        print("Data:", d)
    except Exception as e:
        print(f"Error: {e}")
    watch.stop()

    print(f"Время выполнения: {watch}")
    print("Base URL:", TEST_PRODUCT_URL.base_url)