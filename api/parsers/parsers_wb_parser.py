import json
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

def setup_selenium():
    """Initialize Selenium with headless Chrome."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    try:
        driver = webdriver.Chrome(options=options)
        logger.info("Selenium initialized successfully")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Selenium: {e}")
        return None

def scrape_wildberries(query):
    """Scrape Wildberries search results for the query across 5 pages."""
    driver = setup_selenium()
    if not driver:
        logger.error("Cannot proceed without Selenium")
        return []

    encoded_query = query.replace(" ", "+")
    base_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={encoded_query}"
    logger.info(f"Starting scrape for query: {query}")

    products = []
    max_pages = 5
    current_page = 1

    try:
        while current_page <= max_pages:
            page_url = f"{base_url}&page={current_page}"
            driver.get(page_url)
            logger.info(f"Scraping page {current_page}")

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "product-card"))
            )

            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            product_cards = driver.find_elements(By.CLASS_NAME, "product-card")
            logger.info(f"Found {len(product_cards)} product cards on page {current_page}")

            for index, card in enumerate(product_cards, len(products) + 1):
                try:
                    product = {}
                    product["index"] = index

                    product["article"] = card.get_attribute("data-nm-id") or ""

                    title_elem = card.find_element(
                        By.CSS_SELECTOR, "span.product-card__name"
                    )
                    product["title"] = title_elem.text.strip() if title_elem else ""

                    price_elem = card.find_element(
                        By.CSS_SELECTOR, "ins.price__lower-price"
                    )
                    product["price"] = price_elem.text.strip().replace("\u2009", "").replace("₽", "").strip() if price_elem else ""

                    link_elem = card.find_element(By.CSS_SELECTOR, "a.product-card__link")
                    product["link"] = link_elem.get_attribute("href") if link_elem else ""

                    if product["article"] and product["title"] and product["price"] and product["link"]:
                        products.append(product)
                        logger.debug(
                            f"Added product: {product['title']} (Article: {product['article']}, Link: {product['link']})"
                        )
                    else:
                        logger.debug(
                            f"Skipped product: title={product['title']}, "
                            f"article={product['article']}, price={product['price']}, link={product['link']}"
                        )

                except Exception as e:
                    logger.error(f"Error parsing product card {index} on page {current_page}: {e}")
                    continue

            current_page += 1
            time.sleep(1)

    except Exception as e:
        logger.error(f"Error during scraping: {e}")
    finally:
        driver.quit()
        logger.info("Selenium driver closed")

    return products