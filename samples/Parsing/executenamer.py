import json
import logging
import time
import random
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import re

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

def setup_selenium():
    """Инициализация Selenium."""
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--start-maximized")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors=true")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            """
        })
        logger.info("Selenium инициализирован")
        return driver
    except Exception as e:
        logger.error(f"Ошибка инициализации Selenium: {e}")
        return None

def scroll_page(driver):
    """Прокрутка страницы для загрузки контента."""
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(random.uniform(0.1, 0.2))
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        logger.debug("Страница прокручена")
    except Exception as e:
        logger.error(f"Ошибка при прокрутке: {e}")

def clean_title(title):
    """Очистка названия от мусора."""
    if not title:
        return None
    title = re.sub(r'\s+', ' ', title.strip())
    title = re.sub(r'[-|].*', '', title).strip()
    return title if title else None

def extract_title_selenium(driver, url):
    """Извлечение названия через Selenium."""
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        scroll_page(driver)

        # 1. Мета-теги
        meta_selectors = [
            "meta[property='og:title']",
            "meta[name='title']",
            "meta[name='twitter:title']",
            "meta[itemprop='name']"
        ]
        for selector in meta_selectors:
            try:
                meta = driver.find_element(By.CSS_SELECTOR, selector)
                title = meta.get_attribute("content")
                if title:
                    logger.debug(f"Найдено в {selector}: {title}")
                    return clean_title(title)
            except:
                continue

        # 2. Заголовок страницы
        try:
            title = driver.find_element(By.CSS_SELECTOR, "title").text
            if title:
                logger.debug(f"Найдено в <title>: {title}")
                return clean_title(title)
        except:
            pass

        # 3. Заголовки h1, h2
        for tag in ["h1", "h2"]:
            try:
                header = driver.find_element(By.CSS_SELECTOR, tag).text
                if header:
                    logger.debug(f"Найдено в {tag}: {header}")
                    return clean_title(header)
            except:
                continue

        # 4. Классы product-title, name и т.д.
        class_selectors = [
            "[class*='product-title']",
            "[class*='item-title']",
            "[class*='name']",
            "[class*='title']",
            "[class*='product-name']"
        ]
        for selector in class_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector).text
                if elem:
                    logger.debug(f"Найдено в {selector}: {elem}")
                    return clean_title(elem)
            except:
                continue

        # 5. JSON-LD
        try:
            scripts = driver.find_elements(By.CSS_SELECTOR, "script[type='application/ld+json']")
            for script in scripts:
                json_data = json.loads(script.get_attribute("innerHTML"))
                if isinstance(json_data, dict) and json_data.get("name"):
                    logger.debug(f"Найдено в JSON-LD: {json_data['name']}")
                    return clean_title(json_data["name"])
                elif isinstance(json_data, list):
                    for item in json_data:
                        if item.get("name"):
                            logger.debug(f"Найдено в JSON-LD: {item['name']}")
                            return clean_title(item["name"])
        except:
            pass

        # 6. XPath как запасной
        try:
            elem = driver.find_element(By.XPATH, "//*[contains(@class, 'title') or contains(@class, 'name')]")
            title = elem.text
            if title:
                logger.debug(f"Найдено через XPath: {title}")
                return clean_title(title)
        except:
            pass

        logger.error("Название не найдено через Selenium")
        return None
    except Exception as e:
        logger.error(f"Ошибка Selenium: {e}")
        return None

def extract_title_requests(url):
    """Извлечение названия через requests."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 1. Мета-теги
        meta_tags = [
            ("meta[property='og:title']", "content"),
            ("meta[name='title']", "content"),
            ("meta[name='twitter:title']", "content"),
            ("meta[itemprop='name']", "content")
        ]
        for selector, attr in meta_tags:
            tag = soup.select_one(selector)
            if tag and tag.get(attr):
                logger.debug(f"Найдено в {selector}: {tag.get(attr)}")
                return clean_title(tag.get(attr))

        # 2. Заголовок страницы
        title_tag = soup.select_one("title")
        if title_tag and title_tag.text:
            logger.debug(f"Найдено в <title>: {title_tag.text}")
            return clean_title(title_tag.text)

        # 3. Заголовки h1, h2
        for tag in ["h1", "h2"]:
            header = soup.select_one(tag)
            if header and header.text:
                logger.debug(f"Найдено в {tag}: {header.text}")
                return clean_title(header.text)

        # 4. Классы
        class_selectors = [
            "[class*='product-title']",
            "[class*='item-title']",
            "[class*='name']",
            "[class*='title']",
            "[class*='product-name']"
        ]
        for selector in class_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text:
                logger.debug(f"Найдено в {selector}: {elem.text}")
                return clean_title(elem.text)

        # 5. JSON-LD
        scripts = soup.select("script[type='application/ld+json']")
        for script in scripts:
            try:
                json_data = json.loads(script.text)
                if isinstance(json_data, dict) and json_data.get("name"):
                    logger.debug(f"Найдено в JSON-LD: {json_data['name']}")
                    return clean_title(json_data["name"])
                elif isinstance(json_data, list):
                    for item in json_data:
                        if item.get("name"):
                            logger.debug(f"Найдено в JSON-LD: {item['name']}")
                            return clean_title(item["name"])
            except:
                continue

        logger.error("Название не найдено через requests")
        return None
    except Exception as e:
        logger.error(f"Ошибка requests: {e}")
        return None

def get_product_title(url):
    """Основная функция для извлечения названия."""
    logger.info(f"Обрабатываю URL: {url}")

    # Попробуем через requests
    title = extract_title_requests(url)
    if title:
        logger.info(f"Успешно найдено название: {title}")
        return {"url": url, "title": title}

    # Если requests не сработал, пробуем Selenium
    driver = setup_selenium()
    if not driver:
        logger.error("Не удалось запустить Selenium")
        return {"url": url, "title": None}

    try:
        title = extract_title_selenium(driver, url)
        if title:
            logger.info(f"Успешно найдено название: {title}")
            return {"url": url, "title": title}
        else:
            logger.error("Название не найдено")
            return {"url": url, "title": None}
    finally:
        try:
            driver.quit()
            logger.info("Selenium закрыт")
        except:
            pass

def save_to_json(data):
    """Сохранение в JSON."""
    try:
        with open("product_title.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info("Результат сохранён в product_title.json")
    except Exception as e:
        logger.error(f"Ошибка сохранения JSON: {e}")

def main():
    url = input("Введите URL товара: ")
    result = get_product_title(url)
    save_to_json(result)

if __name__ == "__main__":
    main()