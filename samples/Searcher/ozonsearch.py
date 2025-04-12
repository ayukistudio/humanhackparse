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

def scrape_ozon(query):
    """Scrape Ozon search results for 60 seconds."""
    driver = setup_selenium()
    if not driver:
        logger.error("Cannot proceed without Selenium")
        return []

    encoded_query = query.replace(" ", "+")
    base_url = f"https://www.ozon.ru/search/?from_global=true&text={encoded_query}"
    logger.info(f"Starting scrape for query: {query}")

    products = []
    max_pages = 5
    current_page = 1
    start_time = time.time()
    max_duration = 60  # 60 секунд

    while current_page <= max_pages and (time.time() - start_time) < max_duration:
        remaining_time = max_duration - (time.time() - start_time)
        if remaining_time <= 0:
            break

        page_url = f"{base_url}&page={current_page}"
        logger.info(f"Scraping page {current_page}")

        try:
            driver.get(page_url)
            time.sleep(random.uniform(1, 2))

            # Проверка на CAPTCHA
            captcha = driver.find_elements(By.CSS_SELECTOR, "div.captcha-container")
            if captcha:
                logger.error("CAPTCHA detected, stopping")
                break

            # Ожидание загрузки товаров
            try:
                WebDriverWait(driver, min(15, remaining_time)).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.tile-root"))
                )
            except TimeoutException:
                logger.error(f"Timeout loading products on page {current_page}")
                current_page += 1
                continue

            # Прокрутка страницы
            scroll_to_bottom(driver, max_scroll_time=min(10, remaining_time))

            # Поиск карточек товаров
            product_tiles = driver.find_elements(By.CSS_SELECTOR, "div.tile-root")
            logger.info(f"Found {len(product_tiles)} product tiles on page {current_page}")

            for tile in product_tiles:
                product = {
                    "title": None,
                    "price": None,
                    "link": None,
                    "image": None,
                    "article": None
                }

                # Название
                try:
                    title_elem = tile.find_element(By.CSS_SELECTOR, "span[class*='tsBody'][class*='Medium']")
                    product["title"] = title_elem.text.strip() if title_elem else None
                except:
                    pass

                # Цена
                try:
                    price_elem = tile.find_element(By.CSS_SELECTOR, "span[class*='tsHeadline'][class*='Medium']")
                    product["price"] = price_elem.text.strip().replace("\u2009", "").replace("₽", "").strip() if price_elem else None
                except:
                    pass

                # Ссылка
                try:
                    link_elem = tile.find_element(By.CSS_SELECTOR, "a[class*='tile-hover-target'], a[href*='/product/']")
                    href = link_elem.get_attribute("href")
                    product["link"] = href if href and "/product/" in href else None
                except:
                    try:
                        # Альтернативный поиск любой ссылки в карточке
                        link_elem = tile.find_element(By.CSS_SELECTOR, "a")
                        href = link_elem.get_attribute("href")
                        product["link"] = href if href and "/product/" in href else None
                    except:
                        pass

                # Артикул
                if product["link"]:
                    try:
                        # Извлекаем ID из ссылки (например, /product/1855045065)
                        article_id = product["link"].split("/product/")[-1].split("-")[0].split("?")[0]
                        product["article"] = article_id if article_id.isdigit() else None
                    except:
                        pass
                else:
                    try:
                        # Проверяем атрибуты data-sku или data-product-id
                        article_elem = tile.find_element(By.CSS_SELECTOR, "div[data-widget='webProduct']")
                        article_id = article_elem.get_attribute("data-sku") or article_elem.get_attribute("data-product-id")
                        product["article"] = article_id if article_id and article_id.isdigit() else None
                    except:
                        pass

                # Картинка
                try:
                    img_elem = tile.find_element(By.CSS_SELECTOR, "img")
                    product["image"] = img_elem.get_attribute("src") if img_elem else None
                except:
                    pass

                products.append(product)
                logger.debug(
                    f"Added product: title={product['title']}, price={product['price']}, "
                    f"link={product['link']}, image={product['image']}, article={product['article']}"
                )

            current_page += 1
            time.sleep(random.uniform(2, 3))

        except Exception as e:
            logger.error(f"Error on page {current_page}: {e}")
            current_page += 1
            continue

    try:
        driver.quit()
    except:
        pass
    logger.info("Selenium driver closed")

    return products

def save_to_json(products):
    """Save products to ozonparse.json."""
    try:
        with open("ozonparse.json", "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=4)
        logger.info("Results saved to ozonparse.json")
    except Exception as e:
        logger.error(f"Error saving to JSON: {e}")

def main():
    query = input("Введите название товара для поиска на Ozon: ")
    products = scrape_ozon(query)
    
    save_to_json(products)
    logger.info(f"Found and saved {len(products)} products")

if __name__ == "__main__":
    main()