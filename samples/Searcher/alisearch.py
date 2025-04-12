import json
import logging
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Set up logging
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
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--start-maximized")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    options.add_argument("--disable-cache")
    options.add_argument("--disk-cache-size=0")
    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("Selenium initialized successfully")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Selenium: {e}")
        return None

def scroll_to_bottom(driver, max_scroll_time=10):
    """Полная прокрутка страницы до конца с ограничением времени."""
    start_time = time.time()
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        while time.time() - start_time < max_scroll_time:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1, 2))
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        logger.debug("Page fully scrolled")
    except Exception as e:
        logger.error(f"Error scrolling page: {e}")

def scrape_aliexpress(query):
    """Scrape AliExpress search results for 60 seconds."""
    driver = setup_selenium()
    if not driver:
        logger.error("Cannot proceed without Selenium")
        return []

    encoded_query = query.replace(" ", "+")
    base_url = f"https://aliexpress.ru/wholesale?SearchText={encoded_query}&g=y&page=1"
    logger.info(f"Starting scrape for query: {query}")

    products = []
    start_time = time.time()
    max_duration = 60  # 60 секунд
    max_retries = 2  # Повторные попытки загрузки

    try:
        logger.info("Scraping page 1")
        for attempt in range(max_retries + 1):
            try:
                driver.get(base_url)
                time.sleep(random.uniform(1, 2))

                # Проверка на CAPTCHA
                captcha = driver.find_elements(By.CSS_SELECTOR, "div.captcha-container, div[class*='captcha']")
                if captcha:
                    logger.error("CAPTCHA detected, stopping")
                    return products

                # Ожидание загрузки товаров
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='red-snippet_RedSnippet__']"))
                )
                break
            except TimeoutException:
                logger.error(f"Timeout loading products, attempt {attempt + 1}/{max_retries + 1}")
                if attempt == max_retries:
                    logger.error("Failed to load products after all retries")
                    return products
                time.sleep(random.uniform(2, 3))

        # Прокрутка страницы
        scroll_to_bottom(driver, max_scroll_time=min(15, max_duration - (time.time() - start_time)))

        # Поиск карточек товаров
        product_tiles = driver.find_elements(By.CSS_SELECTOR, "div[class*='red-snippet_RedSnippet__trustAndTitle__']")
        if not product_tiles:
            logger.info("No product containers found, trying fallback selector")
            product_tiles = driver.find_elements(By.CSS_SELECTOR, "div[class*='red-snippet_RedSnippet__']")
        logger.info(f"Found {len(product_tiles)} product tiles")

        for tile in product_tiles:
            if (time.time() - start_time) >= max_duration:
                break

            product = {
                "title": None,
                "price": None,
                "link": None,
                "image": None,
                "article": None
            }

            # Найти родительскую карточку
            try:
                card = tile.find_element(By.XPATH, "./ancestor::div[contains(@class, 'red-snippet_RedSnippet__')]") or tile
            except:
                card = tile

            # Ссылка
            try:
                link_elem = card.find_element(By.CSS_SELECTOR, "a[href*='/item/']")
                href = link_elem.get_attribute("href")
                product["link"] = href if href else None
            except:
                pass

            # Артикул
            if product["link"]:
                try:
                    article_id = product["link"].split("/item/")[-1].split(".html")[0]
                    product["article"] = article_id if article_id.isdigit() else None
                except:
                    pass
            else:
                try:
                    article_id = card.get_attribute("data-product-id")
                    product["article"] = article_id if article_id and article_id.isdigit() else None
                except:
                    pass

            # Название
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, "div[class*='red-snippet_RedSnippet__title__']")
                product["title"] = title_elem.text.strip() if title_elem else None
            except:
                pass

            # Цена
            try:
                price_elem = card.find_element(By.CSS_SELECTOR, "div[class*='red-snippet_RedSnippet__priceNew__']")
                product["price"] = price_elem.text.strip().replace("\u2009", "").replace("₽", "").strip() if price_elem else None
            except:
                pass

            # Картинка
            try:
                img_elem = card.find_element(By.CSS_SELECTOR, "img")
                product["image"] = img_elem.get_attribute("src") if img_elem else None
            except:
                pass

            products.append(product)
            logger.debug(
                f"Added product: title={product['title']}, price={product['price']}, "
                f"link={product['link']}, image={product['image']}, article={product['article']}"
            )

    except Exception as e:
        logger.error(f"Error during scraping: {e}")

    try:
        driver.quit()
    except:
        pass
    logger.info("Selenium driver closed")

    return products

def save_to_json(products):
    """Save products to aliexparse.json."""
    try:
        with open("aliexparse.json", "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=4)
        logger.info("Results saved to aliexparse.json")
    except Exception as e:
        logger.error(f"Error saving to JSON: {e}")

def main():
    query = input("Введите название товара для поиска на AliExpress: ")
    products = scrape_aliexpress(query)
    
    save_to_json(products)
    logger.info(f"Found and saved {len(products)} products")

if __name__ == "__main__":
    main()