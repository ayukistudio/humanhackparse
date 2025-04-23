from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import appwrite
from appwrite.client import Client
from appwrite.services.databases import Databases
from datetime import datetime
import asyncio
import re
from contextlib import asynccontextmanager
import logging
import requests
from bs4 import BeautifulSoup
import json
import time
import random


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(module)s:%(lineno)d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("price_tracker.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

APPWRITE_ENDPOINT = "https://cloud.appwrite.io/v1"
APPWRITE_PROJECT_ID = "nuxt-crm-kanban"
APPWRITE_API_KEY = "standard_58904d3be75745d6d27a775847758d4f34cdd6018421e5df58b7fa72546d75deba9d7537d97bb5fd2dd92173e23504f518c48c42e28d69febdb068ed183a43ea45448463810a76969062a560a0b79dce8a42cc4f07670523e2e1d04dc6c78208545a49e7e908d3703a8213c27021fd6e006ec3dcf3d71bf74d3b77cc0cafd31a"
DATABASE_ID = "crm-base"
COLLECTION_ID = "products-track"

# Initialize Appwrite client
client = Client()
client.set_endpoint(APPWRITE_ENDPOINT)
client.set_project(APPWRITE_PROJECT_ID)
client.set_key(APPWRITE_API_KEY)
databases = Databases(client)

class ProductRequest(BaseModel):
    url: str
    user_id: str

def setup_selenium():
    logger.debug("Начало настройки Selenium WebDriver")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
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
        logger.debug("Инициализация Chrome WebDriver")
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        logger.debug("Установка скрипта для сокрытия WebDriver")
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            """
        })
        logger.info("Selenium успешно инициализирован")
        return driver
    except Exception as e:
        logger.error(f"Ошибка инициализации Selenium: {str(e)}", exc_info=True)
        return None

def scroll_page(driver):
    logger.debug("Начало прокрутки страницы")
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        logger.debug(f"Начальная высота страницы: {last_height}")
        for i in range(3):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(random.uniform(0.1, 0.2))
            new_height = driver.execute_script("return document.body.scrollHeight")
            logger.debug(f"Прокрутка {i+1}, новая высота: {new_height}")
            if new_height == last_height:
                logger.debug("Достигнут конец страницы")
                break
            last_height = new_height
        logger.info("Прокрутка страницы завершена")
    except Exception as e:
        logger.error(f"Ошибка при прокрутке страницы: {str(e)}", exc_info=True)

def clean_title(title):
    if not title:
        logger.debug("Пустое название, возвращается None")
        return None
    logger.debug(f"Исходное название: {title}")
    title = re.sub(r'\s+', ' ', title.strip())
    title = re.sub(r'[-|].*', '', title).strip()
    cleaned = title if title else None
    logger.debug(f"Очищенное название: {cleaned}")
    return cleaned

def extract_title_selenium(url: str) -> Optional[str]:
    logger.info(f"Начало извлечения названия через Selenium для URL: {url}")
    driver = setup_selenium()
    if not driver:
        logger.error("Не удалось инициализировать Selenium")
        return None
    try:
        logger.debug(f"Попытка загрузки страницы: {url}")
        start_time = time.time()
        driver.get(url)
        logger.debug(f"Время загрузки страницы: {time.time() - start_time:.2f} секунд")
        
        logger.debug("Ожидание полной загрузки страницы")
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        logger.debug("Страница полностью загружена")
        scroll_page(driver)

        meta_selectors = [
            "meta[property='og:title']",
            "meta[name='title']",
            "meta[name='twitter:title']",
            "meta[itemprop='name']"
        ]
        for selector in meta_selectors:
            try:
                logger.debug(f"Проверка селектора: {selector}")
                meta = driver.find_element(By.CSS_SELECTOR, selector)
                title = meta.get_attribute("content")
                if title:
                    logger.info(f"Название найдено в {selector}: {title}")
                    return clean_title(title)
            except:
                logger.debug(f"Селектор {selector} не найден")
                continue

        try:
            logger.debug("Проверка тега <title>")
            title = driver.find_element(By.CSS_SELECTOR, "title").text
            if title:
                logger.info(f"Название найдено в <title>: {title}")
                return clean_title(title)
        except:
            logger.debug("Тег <title> не найден")

        for tag in ["h1", "h2"]:
            try:
                logger.debug(f"Проверка тега {tag}")
                header = driver.find_element(By.CSS_SELECTOR, tag).text
                if header:
                    logger.info(f"Название найдено в {tag}: {header}")
                    return clean_title(header)
            except:
                logger.debug(f"Тег {tag} не найден")
                continue

        class_selectors = [
            "[class*='product-title']",
            "[class*='item-title']",
            "[class*='name']",
            "[class*='title']",
            "[class*='product-name']"
        ]
        for selector in class_selectors:
            try:
                logger.debug(f"Проверка селектора класса: {selector}")
                elem = driver.find_element(By.CSS_SELECTOR, selector).text
                if elem:
                    logger.info(f"Название найдено в {selector}: {elem}")
                    return clean_title(elem)
            except:
                logger.debug(f"Селектор класса {selector} не найден")
                continue

        try:
            logger.debug("Проверка JSON-LD")
            scripts = driver.find_elements(By.CSS_SELECTOR, "script[type='application/ld+json']")
            for script in scripts:
                json_data = json.loads(script.get_attribute("innerHTML"))
                if isinstance(json_data, dict) and json_data.get("name"):
                    logger.info(f"Название найдено в JSON-LD: {json_data['name']}")
                    return clean_title(json_data["name"])
                elif isinstance(json_data, list):
                    for item in json_data:
                        if item.get("name"):
                            logger.info(f"Название найдено в JSON-LD: {item['name']}")
                            return clean_title(item["name"])
        except:
            logger.debug("JSON-LD не найден или невалидный")

        try:
            logger.debug("Проверка через XPath")
            elem = driver.find_element(By.XPATH, "//*[contains(@class, 'title') or contains(@class, 'name')]")
            title = elem.text
            if title:
                logger.info(f"Название найдено через XPath: {title}")
                return clean_title(title)
        except:
            logger.debug("XPath не сработал")

        logger.warning(f"Название не найдено через Selenium для URL: {url}")
        return None
    except TimeoutException as e:
        logger.error(f"Таймаут при загрузке страницы {url}: {str(e)}", exc_info=True)
        return None
    except WebDriverException as e:
        logger.error(f"Ошибка WebDriver для {url}: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Общая ошибка при извлечении через Selenium: {str(e)}", exc_info=True)
        return None
    finally:
        try:
            logger.debug("Закрытие Selenium WebDriver")
            driver.quit()
        except:
            logger.error("Ошибка при закрытии Selenium")

def extract_title_requests(url: str) -> Optional[str]:
    logger.info(f"Начало извлечения названия через requests для URL: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    try:
        logger.debug("Отправка HTTP-запроса")
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        logger.debug(f"Время ответа HTTP: {time.time() - start_time:.2f} секунд")
        logger.debug("Страница успешно загружена через requests")
        soup = BeautifulSoup(response.text, "html.parser")
        
        meta_tags = [
            ("meta[property='og:title']", "content"),
            ("meta[name='title']", "content"),
            ("meta[name='twitter:title']", "content"),
            ("meta[itemprop='name']", "content")
        ]
        for selector, attr in meta_tags:
            logger.debug(f"Проверка мета-тега: {selector}")
            tag = soup.select_one(selector)
            if tag and tag.get(attr):
                logger.info(f"Название найдено в {selector}: {tag.get(attr)}")
                return clean_title(tag.get(attr))
            logger.debug(f"Мета-тег {selector} не найден")

        logger.debug("Проверка тега <title>")
        title_tag = soup.select_one("title")
        if title_tag and title_tag.text:
            logger.info(f"Название найдено в <title>: {title_tag.text}")
            return clean_title(title_tag.text)
        logger.debug("Тег <title> не найден")

        for tag in ["h1", "h2"]:
            logger.debug(f"Проверка тега {tag}")
            header = soup.select_one(tag)
            if header and header.text:
                logger.info(f"Название найдено в {tag}: {header.text}")
                return clean_title(header.text)
            logger.debug(f"Тег {tag} не найден")

        class_selectors = [
            "[class*='product-title']",
            "[class*='item-title']",
            "[class*='name']",
            "[class*='title']",
            "[class*='product-name']"
        ]
        for selector in class_selectors:
            logger.debug(f"Проверка селектора класса: {selector}")
            try:
                elem = soup.select_one(selector)
                if elem and elem.text:
                    logger.info(f"Название найдено в {selector}: {elem.text}")
                    return clean_title(elem.text)
            except:
                logger.debug(f"Селектор класса {selector} не найден")
                continue

        logger.debug("Проверка JSON-LD")
        scripts = soup.select("script[type='application/ld+json']")
        for script in scripts:
            try:
                json_data = json.loads(script.text)
                if isinstance(json_data, dict) and json_data.get("name"):
                    logger.info(f"Название найдено в JSON-LD: {json_data['name']}")
                    return clean_title(json_data["name"])
                elif isinstance(json_data, list):
                    for item in json_data:
                        if item.get("name"):
                            logger.info(f"Название найдено в JSON-LD: {item['name']}")
                            return clean_title(item["name"])
            except:
                logger.debug("JSON-LD невалидный или отсутствует")
                continue

        logger.warning(f"Название не найдено через requests для URL: {url}")
        return None
    except requests.exceptions.Timeout:
        logger.error(f"Таймаут HTTP-запроса для {url}", exc_info=True)
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка HTTP-запроса для {url}: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Общая ошибка при извлечении через requests: {str(e)}", exc_info=True)
        return None

def extract_price(url: str) -> Optional[float]:
    driver = setup_selenium()
    if not driver:
        logger.error("Не удалось инициализировать Selenium для извлечения цены")
        return None
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        
        price = None
        if 'ozon.ru' in url:
            price_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-widget='webPrice'] span")))
            price = price_element.text
        elif 'wildberries.ru' in url:
            price_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".price-block__final-price")))
            price = price_element.text
        elif 'megamarket.ru' in url:
            price_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".pdp-price__current")))
            price = price_element.text
        else:
            logger.warning(f"Unsupported URL: {url}")
            return None

        price = re.sub(r'[^\d]', '', price) if price else None
        if price:
            logger.info(f"Extracted price {price} for URL: {url}")
        return float(price) if price else None
    
    except Exception as e:
        logger.error(f"Error extracting price for URL {url}: {e}", exc_info=True)
        return None
    finally:
        try:
            driver.quit()
        except:
            logger.error("Ошибка при закрытии Selenium при извлечении цены")

async def update_price_periodically(url: str, user_id: str):
    while True:
        price = extract_price(url)
        title = extract_title_requests(url)
        if not title:
            logger.debug("Название не найдено через requests, пробуем Selenium")
            title = extract_title_selenium(url)
        
        if price:
            current_time = datetime.now()
            document = {
                'user_id': user_id,
                'url': url,
                'date': current_time.strftime('%Y-%m-%d'),
                'time': current_time.strftime('%H:%M:%S'),
                'price': price,
                'title': title or ''
            }
            try:
                databases.create_document(
                    database_id=DATABASE_ID,
                    collection_id=COLLECTION_ID,
                    document_id='unique()',
                    data=document
                )
                logger.info(f"Price updated for URL: {url}, user_id: {user_id}, price: {price}, title: {title}, time: {current_time}")
            except Exception as e:
                logger.error(f"Error saving to Appwrite for URL {url}, user_id: {user_id}: {e}", exc_info=True)
        
        await asyncio.sleep(1 * 60 * 60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        databases.get_collection(database_id=DATABASE_ID, collection_id=COLLECTION_ID)
        
        attributes = databases.list_attributes(database_id=DATABASE_ID, collection_id=COLLECTION_ID)
        existing_attributes = {attr['key'] for attr in attributes['attributes']}
        
        if 'user_id' not in existing_attributes:
            databases.create_string_attribute(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID,
                key="user_id",
                size=255,
                required=True
            )
        if 'url' not in existing_attributes:
            databases.create_string_attribute(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID,
                key="url",
                size=1000,
                required=True
            )
        if 'date' not in existing_attributes:
            databases.create_string_attribute(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID,
                key="date",
                size=10,
                required=True
            )
        if 'time' not in existing_attributes:
            databases.create_string_attribute(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID,
                key="time",
                size=8,
                required=True
            )
        if 'price' not in existing_attributes:
            databases.create_float_attribute(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID,
                key="price",
                required=True
            )
        if 'title' not in existing_attributes:
            databases.create_string_attribute(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID,
                key="title",
                size=500,
                required=False
            )
        logger.info("Collection attributes verified for products-track")
    except Exception as e:
        logger.error(f"Error setting up collection attributes: {e}", exc_info=True)

    yield
    logger.info("Shutting down...")

app.lifespan = lifespan

@app.post("/track-price")
async def track_price(request: ProductRequest, background_tasks: BackgroundTasks):
    price = extract_price(request.url)
    if not price:
        logger.warning(f"Failed to extract price for URL: {request.url}")
        return {"error": "Could not extract price"}

    title = extract_title_requests(request.url)
    if not title:
        logger.debug("Название не найдено через requests, пробуем Selenium")
        title = extract_title_selenium(request.url)
    logger.debug(f"Title extracted for URL: {request.url}: {title}")

    current_time = datetime.now()
    document = {
        'user_id': request.user_id,
        'url': request.url,
        'date': current_time.strftime('%Y-%m-%d'),
        'time': current_time.strftime('%H:%M:%S'),
        'price': price,
        'title': title or '' 
    }

    try:
        databases.create_document(
            database_id=DATABASE_ID,
            collection_id=COLLECTION_ID,
            document_id='unique()',
            data=document
        )
        logger.info(f"Initial price saved for URL: {request.url}, user_id: {request.user_id}, price: {price}, title: {title}")
        
        background_tasks.add_task(update_price_periodically, request.url, request.user_id)
        
        return {"message": "Price tracking started", "initial_price": price, "title": title}
    except Exception as e:
        logger.error(f"Failed to save initial data for URL: {request.url}, user_id: {request.user_id}: {e}", exc_info=True)
        return {"error": f"Failed to save data: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
