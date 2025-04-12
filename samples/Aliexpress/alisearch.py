import requests
from bs4 import BeautifulSoup
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_aliexpress(search_query, page=1):
    # Construct the search URL
    base_url = "https://aliexpress.ru/wholesale"
    params = {
        "SearchText": search_query,
        "g": "y",
        "page": page
    }
    url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    logging.info(f"Scraping page {page}: {url}")

    # Send request with headers to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch page: {e}")
        return []

    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    products = []

    # Debugging: Save HTML to inspect
    with open(f"aliexpress_page_{page}.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    logging.info(f"Saved HTML to aliexpress_page_{page}.html for debugging")

    # Find product containers
    # Try a more flexible selector based on the HTML snippet
    product_containers = soup.find_all('div', class_=lambda x: x and 'red-snippet_RedSnippet__trustAndTitle__e15tmk' in x)
    if not product_containers:
        logging.info("No product containers found with 'red-snippet_RedSnippet__trustAndTitle__e15tmk'.")
        # Fallback: Look for any div with a title class
        product_containers = soup.find_all('div', class_='red-snippet_RedSnippet__title__e15tmk')
        logging.info(f"Found {len(product_containers)} containers with 'red-snippet_RedSnippet__title__e15tmk'.")

    for container in product_containers:
        try:
            product = {}
            # Find the parent card to ensure we get all related elements
            card = container.find_parent('div', class_=lambda x: x and 'red-snippet_RedSnippet__' in x) or container

            # Product URL (look for the closest anchor tag)
            link = card.find('a', href=True)
            product['url'] = link['href'] if link and 'href' in link.attrs else ''

            # Title
            title_elem = card.find('div', class_='red-snippet_RedSnippet__title__e15tmk')
            product['title'] = title_elem.get_text(strip=True) if title_elem else ''
            logging.debug(f"Title found: {product['title']}")

            # Current price
            price_new_elem = card.find('div', class_='red-snippet_RedSnippet__priceNew__e15tmk')
            product['price_new'] = price_new_elem.get_text(strip=True).replace('\xa0', '') if price_new_elem else ''
            logging.debug(f"Price new found: {product['price_new']}")

            # Old price
            price_old_elem = card.find('div', class_='red-snippet_RedSnippet__priceOld__e15tmk')
            product['price_old'] = price_old_elem.get_text(strip=True).replace('\xa0', '') if price_old_elem else ''

            # Discount
            discount_elem = card.find('span', string=lambda x: x and '%' in x)
            product['discount'] = discount_elem.get_text(strip=True) if discount_elem else ''

            # Rating
            rating_elem = card.find('div', class_='red-snippet_RedSnippet__trustItem__e15tmk', string=lambda x: x and '.' in x)
            product['rating'] = rating_elem.get_text(strip=True).replace('\xa0', '') if rating_elem else ''

            # Purchases
            purchases_elem = card.find('div', string=lambda x: x and 'купили' in x.lower())
            product['purchases'] = purchases_elem.get_text(strip=True).replace('\xa0', '') if purchases_elem else ''

            # Delivery
            delivery_elem = card.find('div', class_='red-snippet_RedSnippet__deliveryItem__e15tmk')
            product['delivery'] = delivery_elem.get_text(strip=True).replace('\xa0', '') if delivery_elem else ''

            # Validate product
            if product['title'] and product['price_new']:
                products.append(product)
                logging.info(f"Valid product found: {product['title']}")
            else:
                logging.debug(f"Invalid product: title={product['title']}, price_new={product['price_new']}")

        except Exception as e:
            logging.error(f"Error parsing product: {e}")
            continue

    logging.info(f"Found {len(products)} valid products on page {page}.")
    return products

def main():
    search_query = input("Enter search query (e.g., увлажнители воздуха): ")
    page = 1
    products = scrape_aliexpress(search_query, page)

    if products:
        for idx, product in enumerate(products, 1):
            print(f"\nProduct {idx}:")
            print(f"Title: {product['title']}")
            print(f"Price: {product['price_new']}")
            print(f"Old Price: {product['price_old']}")
            print(f"Discount: {product['discount']}")
            print(f"Rating: {product['rating']}")
            print(f"Purchases: {product['purchases']}")
            print(f"Delivery: {product['delivery']}")
            print(f"URL: {product['url']}")
    else:
        print("No products found.")

if __name__ == "__main__":
    main()