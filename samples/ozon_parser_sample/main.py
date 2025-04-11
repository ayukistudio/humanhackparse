import requests
from bs4 import BeautifulSoup
from stopwatch import Stopwatch
from url import Url

TEST_PRODUCT_URL = Url('https://www.ozon.ru/product/1444030137')

cookies = {}

headers = {
    'User-Agent': 'curl/8.8.0',
    # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:131.0) Gecko/20100101 Firefox/131.0',
    'Accept': '*/*'
}

headers2 = {
    'User-Agent': 'curl/8.8.0',
    # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:131.0) Gecko/20100101 Firefox/131.0',
    'Accept': '*/*'
}

def _get_data_product(url: Url) -> tuple:
    if not isinstance(url, Url):
        raise ValueError('URL is invalid.')

    response_ = requests.get(url.full_url, headers=headers, allow_redirects=True)

    soup = BeautifulSoup(response_.content, "html.parser")
    
    name_shop = soup.find('a', class_='kv2_27')
    category = soup.find('ol', class_='je1_10') # je1_10 tsBodyControl400Small
    green_price = soup.find('span', class_='s5m_27 ms4_27')
    main_price = soup.find('span', class_='mt0_27 m0t_27 mt4_27')
    red_price = soup.find('span', class_='mt_27 tm0_27 ms9_27 tm_27')

    if name_shop is None:
        raise AttributeError('green_price')
    if category is None:
        raise AttributeError('green_price')
    if green_price is None:
        raise AttributeError('green_price')
    if main_price is None:
        raise AttributeError('main_price')
    if red_price is None:
        raise AttributeError('red_price')


    return name_shop.text, url.join(name_shop.get("href")), float(green_price.text[:-2]), float(main_price.text[:-2]), float(red_price.text[:-2])

def get_price_product(url: Url) -> tuple[float, float, float]:
    data = _get_data_product(url)
    return data[1], data[2], data[3]

if __name__ == '__main__':
    watch = Stopwatch()

    watch.start()
    # prices = get_price_product(TEST_PRODUCT_URL)
    d = _get_data_product(TEST_PRODUCT_URL)
    watch.stop()

    print(f"Время выполнения: {watch}")
    watch.reset()

    print(d)
    print(TEST_PRODUCT_URL.base_url)
