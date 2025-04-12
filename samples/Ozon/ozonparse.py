import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging
import time
import random
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def normalize_url(url):
    """Ensure the URL is in a valid Ozon product format."""
    url = url.strip()
    # Match product URLs (e.g., /product/123 or /product/name-123)
    if not re.match(r'https?://www\.ozon\.ru/product/.*', url):
        raise ValueError("Invalid Ozon product URL")
    # Normalize to HTTPS
    return url.replace('http://', 'https://')

def scrape_ozon_product(url):
    """Scrape all details from an Ozon product page using a proxy."""
    try:
        url = normalize_url(url)
    except ValueError as e:
        logging.error(f"URL error: {e}")
        return None

    logging.info(f"Scraping Ozon product: {url}")

    # Proxy configuration
    proxy = {
        "http": "http://hkwoioqo:ttfpzwihcdck@38.153.152.244:9594",
        "https": "http://hkwoioqo:ttfpzwihcdck@38.153.152.244:9594"
    }

    # Headers to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

    # Optional cookies
    cookies = {
        "ab_test": str(random.randint(1000, 9999)),  # Randomize to avoid bans
    }

    # Random delay
    time.sleep(random.uniform(1, 3))

    # Fetch the page
    try:
        response = requests.get(url, headers=headers, cookies=cookies, proxies=proxy, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch page: {e}")
        return None

    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # Debugging: Save HTML
    with open("ozon_product.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    logging.info("Saved HTML to ozon_product.html for debugging")

    product = {}
    try:
        # Title
        title_elem = soup.find('h1') or soup.find('div', itemprop='name')
        product['title'] = title_elem.text.strip() if title_elem else ''
        logging.debug(f"Title: {product['title']}")

        # Price (current)
        price_elem = (soup.find('span', class_=lambda x: x and 'price' in x.lower()) or 
                      soup.find('div', class_=lambda x: x and 'price' in x.lower()))
        product['price_current'] = price_elem.text.strip().replace('\xa0', '') if price_elem else ''
        logging.debug(f"Current price: {product['price_current']}")

        # Original price (if discounted)
        orig_price_elem = soup.find('span', class_=lambda x: x and 'original' in x.lower())
        product['price_original'] = orig_price_elem.text.strip().replace('\xa0', '') if orig_price_elem else ''
        logging.debug(f"Original price: {product['price_original']}")

        # Discount
        discount_elem = soup.find('span', class_=lambda x: x and 'discount' in x.lower())
        product['discount'] = discount_elem.text.strip() if discount_elem else ''
        logging.debug(f"Discount: {product['discount']}")

        # Brand
        brand_elem = soup.find('a', class_=lambda x: x and 'brand' in x.lower()) or soup.find('span', itemprop='brand')
        product['brand'] = brand_elem.text.strip() if brand_elem else ''
        logging.debug(f"Brand: {product['brand']}")

        # Description
        desc_elem = soup.find('div', class_=lambda x: x and 'description' in x.lower()) or soup.find('div', itemprop='description')
        product['description'] = desc_elem.text.strip() if desc_elem else ''
        logging.debug(f"Description: {product['description']}")

        # Characteristics
        chars = {}
        char_section = soup.find('div', class_=lambda x: x and 'characteristics' in x.lower()) or soup.find('dl')
        if char_section:
            for item in char_section.find_all(['dt', 'dd']):
                if item.name == 'dt':
                    key = item.text.strip()
                elif item.name == 'dd':
                    chars[key] = item.text.strip()
        product['characteristics'] = chars
        logging.debug(f"Characteristics: {product['characteristics']}")

        # Images
        images = []
        img_section = soup.find('div', class_=lambda x: x and 'gallery' in x.lower()) or soup.find('div', class_=lambda x: x and 'image' in x.lower())
        if img_section:
            for img in img_section.find_all('img', src=True):
                images.append(img['src'])
        product['images'] = images
        logging.debug(f"Images: {product['images']}")

        # Seller
        seller_elem = soup.find('a', class_=lambda x: x and 'seller' in x.lower()) or soup.find('div', class_=lambda x: x and 'seller' in x.lower())
        product['seller'] = seller_elem.text.strip() if seller_elem else 'Ozon'
        logging.debug(f"Seller: {product['seller']}")

        # Rating
        rating_elem = soup.find('span', class_=lambda x: x and 'rating' in x.lower())
        product['rating'] = rating_elem.text.strip() if rating_elem else ''
        logging.debug(f"Rating: {product['rating']}")

        # Reviews
        reviews_elem = soup.find('a', class_=lambda x: x and 'review' in x.lower()) or soup.find('span', class_=lambda x: x and 'review' in x.lower())
        product['reviews'] = reviews_elem.text.strip() if reviews_elem else ''
        logging.debug(f"Reviews: {product['reviews']}")

        # Availability
        avail_elem = soup.find('div', class_=lambda x: x and 'availability' in x.lower()) or soup.find('span', string=lambda x: x and ('в наличии' in x.lower() or 'нет в наличии' in x.lower()))
        product['availability'] = avail_elem.text.strip() if avail_elem else ''
        logging.debug(f"Availability: {product['availability']}")

        # Delivery
        delivery_elem = soup.find('div', class_=lambda x: x and 'delivery' in x.lower())
        product['delivery'] = delivery_elem.text.strip() if delivery_elem else ''
        logging.debug(f"Delivery: {product['delivery']}")

    except Exception as e:
        logging.error(f"Error parsing product card: {e}")
        return None

    # Validate product
    if not product['title']:
        logging.error("No title found; likely an invalid page or CAPTCHA")
        return None

    logging.info(f"Successfully parsed product: {product['title']}")
    return product

def main():
    url = input("Введите ссылку на товар Ozon (например, https://www.ozon.ru/product/1664318790): ")
    product = scrape_ozon_product(url)

    if product:
        print("\nProduct Details:")
        print(f"Title: {product['title']}")
        print(f"Current Price: {product['price_current']}")
        print(f"Original Price: {product['price_original']}")
        print(f"Discount: {product['discount']}")
        print(f"Brand: {product['brand']}")
        print(f"Description: {product['description']}")
        print(f"Characteristics: {product['characteristics']}")
        print(f"Images: {product['images']}")
        print(f"Seller: {product['seller']}")
        print(f"Rating: {product['rating']}")
        print(f"Reviews: {product['reviews']}")
        print(f"Availability: {product['availability']}")
        print(f"Delivery: {product['delivery']}")
    else:
        print("Failed to parse product. Check ozon_product.html for details.")

if __name__ == "__main__":
    main()