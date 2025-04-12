import json
import logging
import time
import random
import socket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger()

def get_random_user_agent():
    """Возвращает случайный User-Agent."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    return random.choice(user_agents)

def check_connection(host="8.8.8.8", port=53, timeout=3):
    """Проверка интернет-соединения."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

def setup_selenium():
    """Инициализация Selenium с настройками."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument(f"user-agent={get_random_user_agent()}")

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("Selenium успешно инициализирован")
        return driver
    except Exception as e:
        logger.error(f"Ошибка инициализации Selenium: {e}")
        return None

def check_captcha(driver):
    """Проверка на наличие CAPTCHA."""
    try:
        captcha = driver.find_elements(By.CSS_SELECTOR, "div.captcha, div[class*='captcha'], div[class*='Checkpoint']")
        if captcha:
            logger.error("Обнаружена CAPTCHA")
            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке CAPTCHA: {e}")
        return False

def scroll_to_bottom(driver, max_scroll_time=10):
    """Плавная прокрутка страницы вниз."""
    start_time = time.time()
    last_height = driver.execute_script("return document.body.scrollHeight")
    while time.time() - start_time < max_scroll_time:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1, 2))
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        ActionChains(driver).move_by_offset(random.randint(1, 50), random.randint(1, 50)).perform()

def handle_popups(driver):
    """Закрытие всплывающих окон и модальных блоков."""
    try:
        current_window = driver.current_window_handle
        for window in driver.window_handles:
            if window != current_window:
                driver.switch_to.window(window)
                driver.close()
        driver.switch_to.window(current_window)

        modal_elements = driver.find_elements(By.CSS_SELECTOR, "div[class*='popup'], div[class*='modal'], div[class*='overlay']")
        for modal in modal_elements:
            try:
                close_button = modal.find_element(By.CSS_SELECTOR, "button, a")
                close_button.click()
                time.sleep(random.uniform(0.5, 1))
            except:
                continue
    except:
        pass

def scrape_yandex(query):
    """Скрапинг Яндекс.Маркета по запросу."""
    if not check_connection():
        logger.error("Нет интернет-соединения.")
        return []

    driver = setup_selenium()
    if not driver:
        return []

    encoded_query = query.replace(" ", "%20")
    base_url = f"https://market.yandex.ru/search?text={encoded_query}&cvredirect=1"
    products = []
    max_pages = 5
    max_duration = 60
    start_time = time.time()

    for current_page in range(1, max_pages + 1):
        if time.time() - start_time > max_duration:
            break

        page_url = f"{base_url}&page={current_page}"
        logger.info(f"Открываем страницу: {page_url}")
        try:
            driver.get(page_url)
            time.sleep(random.uniform(1.5, 3.0))

            if check_captcha(driver):
                break

            handle_popups(driver)

            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-zone-name='snippetList'] div[data-baobab-name='snippet']"))
            )

            scroll_to_bottom(driver)

            product_tiles = driver.find_elements(By.CSS_SELECTOR, "div[data-zone-name='snippetList'] div[data-baobab-name='snippet']")
            logger.info(f"Найдено товаров: {len(product_tiles)}")

            for tile in product_tiles:
                if time.time() - start_time > max_duration:
                    break

                product = {
                    "title": None,
                    "price": None,
                    "link": None,
                    "image": None,
                    "article": None
                }

                try:
                    link_elem = tile.find_element(By.CSS_SELECTOR, "a[href*='/product--']")
                    href = link_elem.get_attribute("href")
                    product["link"] = href
                    product["article"] = href.split("/product--")[-1].split("/")[0]
                except:
                    continue

                try:
                    title_elem = tile.find_element(By.CSS_SELECTOR, "h3[data-zone-name='title'], span[data-auto='snippet-title']")
                    product["title"] = title_elem.text.strip()
                except:
                    pass

                try:
                    price_elem = tile.find_element(By.CSS_SELECTOR, "span[data-auto='mainPrice'], span[class*='price']")
                    product["price"] = price_elem.text.strip().replace("\u2009", "").replace("₽", "").strip()
                except:
                    pass

                try:
                    img_elem = tile.find_element(By.CSS_SELECTOR, "img[class*='image'], img")
                    product["image"] = img_elem.get_attribute("src")
                except:
                    pass

                if product["title"] and product["price"]:
                    products.append(product)

            time.sleep(random.uniform(1.5, 3.0))

        except Exception as e:
            logger.error(f"Ошибка на странице {current_page}: {e}")
            continue

    driver.quit()
    logger.info("Скрапинг завершён. Драйвер закрыт.")
    return products

def save_to_json(products):
    """Сохраняет результат в JSON."""
    try:
        with open("yandexparse.json", "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=4)
        logger.info(f"Сохранено {len(products)} товаров в yandexparse.json")
    except Exception as e:
        logger.error(f"Ошибка при сохранении: {e}")

def main():
    query = input("Введите название товара для поиска на Яндекс.Маркете: ")
    products = scrape_yandex(query)
    save_to_json(products)

if __name__ == "__main__":
    main()
