import json
import logging
import time
import requests
import sys
import os
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import re
from parsers.parsers_ozon_parser import scrape_ozon
from parsers.parsers_sber_parser import scrape_sbermegamarket
from parsers.parsers_wb_parser import scrape_wildberries

# Логирование с самого начала
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(module)s:%(lineno)d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("api_debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
logger.debug("Скрипт запущен, инициализация начата")

app = FastAPI(title="Product Scraper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLRequest(BaseModel):
    url: str

class ScrapeResponse(BaseModel):
    ozon: list
    sbermegamarket: list
    wildberries: list

def check_environment():
    """Проверка окружения."""
    logger.debug("Проверка окружения")
    try:
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Current directory: {os.getcwd()}")
        logger.info(f"Python executable: {sys.executable}")
        logger.info(f"Parser directory exists: {os.path.exists('parsers')}")
        return True
    except Exception as e:
        logger.error(f"Ошибка проверки окружения: {str(e)}", exc_info=True)
        return False

def setup_selenium():
    """Инициализация Selenium."""
    logger.debug("Начало настройки Selenium WebDriver")
    options = Options()
    options.add_argument("--headless=new")
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
    """Прокрутка страницы для загрузки контента."""
    logger.debug("Начало прокрутки страницы")
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(3):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(0.2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logger.debug("Достигнут конец страницы")
                break
            last_height = new_height
        logger.info("Прокрутка страницы завершена")
    except Exception as e:
        logger.error(f"Ошибка при прокрутке страницы: {str(e)}", exc_info=True)

def clean_title(title):
    """Очистка названия от мусора."""
    logger.debug(f"Очистка заголовка: {title}")
    if not title:
        logger.warning("Заголовок пустой")
        return None
    title = re.sub(r'\s+', ' ', title.strip())
    title = re.sub(r'[-|].*', '', title).strip()
    cleaned = title if title else None
    logger.debug(f"Очищенный заголовок: {cleaned}")
    return cleaned

def extract_title_selenium(driver, url):
    """Извлечение названия через Selenium."""
    logger.info(f"Начало извлечения названия через Selenium для URL: {url}")
    try:
        logger.debug(f"Загрузка страницы: {url}")
        driver.get(url)
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        logger.debug("Страница загружена")
        scroll_page(driver)

        meta_selectors = [
            "meta[property='og:title']",
            "meta[name='title']",
            "meta[name='twitter:title']",
            "meta[itemprop='name']"
        ]
        for selector in meta_selectors:
            try:
                logger.debug(f"Поиск мета-тега: {selector}")
                meta = driver.find_element(By.CSS_SELECTOR, selector)
                title = meta.get_attribute("content")
                if title:
                    logger.info(f"Название найдено в {selector}: {title}")
                    return clean_title(title)
            except:
                logger.debug(f"Мета-тег {selector} не найден")
                continue

        try:
            logger.debug("Поиск тега <title>")
            title = driver.find_element(By.CSS_SELECTOR, "title").text
            if title:
                logger.info(f"Название найдено в <title>: {title}")
                return clean_title(title)
        except:
            logger.debug("Тег <title> не найден")

        for tag in ["h1", "h2"]:
            try:
                logger.debug(f"Поиск тега {tag}")
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
                logger.debug(f"Поиск по селектору класса: {selector}")
                elem = driver.find_element(By.CSS_SELECTOR, selector).text
                if elem:
                    logger.info(f"Название найдено в {selector}: {elem}")
                    return clean_title(elem)
            except:
                logger.debug(f"Селектор {selector} не найден")
                continue

        try:
            logger.debug("Поиск JSON-LD скриптов")
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
            logger.debug("JSON-LD не найден или некорректен")

        try:
            logger.debug("Поиск через XPath")
            elem = driver.find_element(By.XPATH, "//*[contains(@class, 'title') or contains(@class, 'name')]")
            title = elem.text
            if title:
                logger.info(f"Название найдено через XPath: {title}")
                return clean_title(title)
        except:
            logger.debug("XPath не нашел подходящих элементов")

        logger.warning("Название не найдено через Selenium")
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

def extract_title_requests(url):
    """Извлечение названия через requests."""
    logger.info(f"Начало извлечения названия через requests для URL: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    try:
        logger.debug(f"Отправка HTTP-запроса к {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        logger.debug("Ответ получен, парсинг HTML")
        soup = BeautifulSoup(response.text, "html.parser")

        meta_tags = [
            ("meta[property='og:title']", "content"),
            ("meta[name='title']", "content"),
            ("meta[name='twitter:title']", "content"),
            ("meta[itemprop='name']", "content")
        ]
        for selector, attr in meta_tags:
            try:
                logger.debug(f"Поиск мета-тега: {selector}")
                tag = soup.select_one(selector)
                if tag and tag.get(attr):
                    logger.info(f"Название найдено в {selector}: {tag.get(attr)}")
                    return clean_title(tag.get(attr))
            except:
                logger.debug(f"Мета-тег {selector} не найден")
                continue

        try:
            logger.debug("Поиск тега <title>")
            title_tag = soup.select_one("title")
            if title_tag and title_tag.text:
                logger.info(f"Название найдено в <title>: {title_tag.text}")
                return clean_title(title_tag.text)
        except:
            logger.debug("Тег <title> не найден")

        for tag in ["h1", "h2"]:
            try:
                logger.debug(f"Поиск тега {tag}")
                header = soup.select_one(tag)
                if header and header.text:
                    logger.info(f"Название найдено в {tag}: {header.text}")
                    return clean_title(header.text)
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
                logger.debug(f"Поиск по селектору класса: {selector}")
                elem = soup.select_one(selector)
                if elem and elem.text:
                    logger.info(f"Название найдено в {selector}: {elem.text}")
                    return clean_title(elem.text)
            except:
                logger.debug(f"Селектор {selector} не найден")
                continue

        try:
            logger.debug("Поиск JSON-LD скриптов")
            scripts = soup.select("script[type='application/ld+json']")
            for script in scripts:
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
            logger.debug("JSON-LD не найден или некорректен")

        logger.warning("Название не найдено через requests")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка HTTP-запроса для {url}: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Общая ошибка при извлечении через requests: {str(e)}", exc_info=True)
        return None

@app.get("/health")
async def health_check():
    """Проверка работоспособности API."""
    logger.info("Получен запрос на проверку работоспособности")
    logger.debug("Отправка ответа: status=healthy")
    return {"status": "healthy", "message": "API is running"}

@app.post("/scrape-products", response_model=ScrapeResponse)
async def scrape_products(request: URLRequest):
    """API endpoint для извлечения названия по URL и парсинга товаров."""
    logger.info(f"Получен запрос на обработку URL: {request.url}")
    start_time = time.time()

    # Валидация URL
    logger.debug("Проверка URL на корректность")
    if not request.url.startswith(("http://", "https://")):
        logger.error("Некорректный URL: отсутствует схема http(s)")
        raise HTTPException(status_code=400, detail="URL должен начинаться с http:// или https://")

    # Извлечение названия
    logger.debug("Попытка извлечения названия через requests")
    title = extract_title_requests(request.url)
    if not title:
        logger.debug("Название не найдено через requests, переход к Selenium")
        driver = setup_selenium()
        if driver:
            try:
                title = extract_title_selenium(driver, request.url)
            finally:
                logger.debug("Закрытие Selenium драйвера")
                driver.quit()
        if not title:
            logger.error("Не удалось извлечь название из URL")
            raise HTTPException(status_code=400, detail="Не удалось извлечь название товара из URL")

    logger.info(f"Извлеченное название: {title}")

    # Запуск парсеров
    logger.debug("Запуск парсеров в многопоточном режиме")
    with ThreadPoolExecutor(max_workers=3) as executor:
        logger.debug("Отправка задачи для Ozon")
        ozon_future = executor.submit(scrape_ozon, title)
        logger.debug("Отправка задачи для SberMegaMarket")
        sber_future = executor.submit(scrape_sbermegamarket, title)
        logger.debug("Отправка задачи для Wildberries")
        wb_future = executor.submit(scrape_wildberries, title)

        logger.debug("Ожидание результатов парсеров")
        results = {
            "ozon": ozon_future.result(),
            "sbermegamarket": sber_future.result(),
            "wildberries": wb_future.result()
        }
        logger.debug(f"Результаты получены: Ozon={len(results['ozon'])}, "
                     f"Sber={len(results['sbermegamarket'])}, WB={len(results['wildberries'])}")

    logger.info(f"Общее время обработки: {time.time() - start_time:.2f} секунд")
    return results

if __name__ == "__main__":
    try:
        logger.debug("Начало выполнения основного блока")
        if not check_environment():
            logger.critical("Ошибка окружения, выход")
            sys.exit(1)
        import uvicorn
        logger.info("Запуск FastAPI сервера на http://0.0.0.0:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {str(e)}", exc_info=True)
        sys.exit(1)