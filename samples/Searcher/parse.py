import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging
import time
import random

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_yandex_market(query):
    # URL-encode the query
    encoded_query = urllib.parse.quote(query)
    # Construct Yandex Market search URL
    url = f"https://market.yandex.ru/search?text={encoded_query}"
    logging.info(f"Searching Yandex Market: {url}")

    # Headers to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    # Optional cookies to simulate a user session
    cookies = {
        "yandexuid": str(random.randint(1000000000, 9999999999)),  # Random user ID
        "i": "some_random_string",  # Placeholder, replace with real cookie if needed
    }

    # Random delay to avoid rate-limiting
    time.sleep(random.uniform(1, 3))

    # Fetch the page
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch page: {e}")
        return []

    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # Debugging: Save HTML
    with open("yandex_market.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    logging.info("Saved HTML to yandex_market.html for debugging")

    products = []
    # Find product cards
    product_cards = soup.find_all('div', class_=lambda x: x and 'snippet-card' in x)

    if not product_cards:
        logging.info("No product cards found with 'snippet-card'.")
        # Fallback: Try broader selector
        product_cards = soup.find_all('div', class_=lambda x: x and 'card' in x.lower())
        logging.info(f"Found {len(product_cards)} alternative containers.")

    for card in product_cards:
        try:
            product = {}
            # Title
            title_elem = card.find('h3') or card.find('span', class_=lambda x: x and 'title' in x.lower())
            product['title'] = title_elem.text.strip() if title_elem else ''
            logging.debug(f"Title found: {product['title']}")

            # URL
            link_elem = card.find('a', href=True)
            product['url'] = f"https://market.yandex.ru{link_elem['href']}" if link_elem and link_elem['href'].startswith('/') else link_elem['href'] if link_elem else ''
            logging.debug(f"URL found: {product['url']}")

            # Price
            price_elem = card.find('span', class_=lambda x: x and 'price' in x.lower()) or card.find('div', class_=lambda x: x and 'price' in x.lower())
            product['price'] = price_elem.text.strip().replace('\xa0', '') if price_elem else ''
            logging.debug(f"Price found: {product['price']}")

            # Store
            store_elem = card.find('div', class_=lambda x: x and 'seller' in x.lower()) or card.find('a', class_=lambda x: x and 'shop' in x.lower())
            product['store'] = store_elem.text.strip() if store_elem else ''
            logging.debug(f"Store found: {product['store']}")

            # Validate product
            if product['title'] and product['url'] and product['price']:
                products.append(product)
                logging.info(f"Valid product found: {product['title']} from {product['store']}")
            else:
                logging.debug(f"Skipped product: title={product['title']}, url={product['url']}, price={product['price']}")

        except Exception as e:
            logging.error(f"Error parsing product card: {e}")
            continue

    logging.info(f"Found {len(products)} valid products.")
    return products

def main():
    query = input("Введите название товара (например, процессор intel core i5): ")
    products = scrape_yandex_market(query)

    if products:
        for idx, product in enumerate(products, 1):
            print(f"\nProduct {idx}:")
            print(f"Title: {product['title']}")
            print(f"Price: {product['price']}")
            print(f"Store: {product['store']}")
            print(f"URL: {product['url']}")
    else:
        print("No products found.")

if __name__ == "__main__":
    main()