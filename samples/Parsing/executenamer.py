import json
import logging
import time
import random
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import re
from typing import Optional

# Настройка логирования с более подробным форматом
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(module)s:%(lineno)d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Product Title Extractor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Укажите адрес Nuxt
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLRequest(BaseModel):
    url: str

class TitleResponse(BaseModel):
    url: str
    title: Optional[str]

def setup_selenium():
    """Инициализация Selenium с дополнительным логированием."""
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
    """Прокрутка страницы для загрузки контента с логированием этапов."""
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
    """Очистка названия от мусора с логированием."""
    if not title:
        logger.debug("Пустое название, возвращается None")
        return None
    logger.debug(f"Исходное название: {title}")
    title = re.sub(r'\s+', ' ', title.strip())
    title = re.sub(r'[-|].*', '', title).strip()
    cleaned = title if title else None
    logger.debug(f"Очищенное название: {cleaned}")
    return cleaned

def extract_title_selenium(driver, url):
    """Извлечение названия через Selenium с подробным логированием."""
    logger.info(f"Начало извлечения названия через Selenium для URL: {url}")
    try:
        logger.debug(f"Попытка загрузки страницы: {url}")
        start_time = time.time()
        driver.get(url)
        logger.debug(f"Время загрузки страницы: {time.time() - start_time:.2f} секунд")
        
        logger.debug("Ожидание полной загрузки страницы")
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        logger.debug("Страница полностью загружена")
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
                logger.debug(f"Проверка селектора: {selector}")
                meta = driver.find_element(By.CSS_SELECTOR, selector)
                title = meta.get_attribute("content")
                if title:
                    logger.info(f"Название найдено в {selector}: {title}")
                    return clean_title(title)
            except:
                logger.debug(f"Селектор {selector} не найден")
                continue

        # 2. Заголовок страницы
        try:
            logger.debug("Проверка тега <title>")
            title = driver.find_element(By.CSS_SELECTOR, "title").text
            if title:
                logger.info(f"Название найдено в <title>: {title}")
                return clean_title(title)
        except:
            logger.debug("Тег <title> не найден")
            pass

        # 3. Заголовки h1, h2
        for tag in ["h1", "h2"]:
            try:
                logger.debug(f"Проверка тега {tag}")
                header = driver.find_element(By.CSS_SELECTOR, tag).text
                if header:
                    logger.info(f"Название найдено в {tag}: {header}")
                    return clean_title(title)
            except:
                logger.debug(f"Тег {tag} не найден")
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
                logger.debug(f"Проверка селектора класса: {selector}")
                elem = driver.find_element(By.CSS_SELECTOR, selector).text
                if elem:
                    logger.info(f"Название найдено в {selector}: {elem}")
                    return clean_title(elem)
            except:
                logger.debug(f"Селектор класса {selector} не найден")
                continue

        # 5. JSON-LD
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
            pass

        # 6. XPath как запасной
        try:
            logger.debug("Проверка через XPath")
            elem = driver.find_element(By.XPATH, "//*[contains(@class, 'title') or contains(@class, 'name')]")
            title = elem.text
            if title:
                logger.info(f"Название найдено через XPath: {title}")
                return clean_title(title)
        except:
            logger.debug("XPath не сработал")
            pass

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
    """Извлечение названия через requests с подробным логированием."""
    logger.info(f"Начало извлечения названия через requests для URL: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    try:
        logger.debug("Отправка HTTP-запроса")
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        logger.debug(f"Время ответа HTTP: {time.time() - start_time:.2f} секунд")
        logger.debug("Страница успешно загружена через requests")
        soup = BeautifulSoup(response.text, "html.parser")

        # 1. Мета-теги
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

        # 2. Заголовок страницы
        logger.debug("Проверка тега <title>")
        title_tag = soup.select_one("title")
        if title_tag and title_tag.text:
            logger.info(f"Название найдено в <title>: {title_tag.text}")
            return clean_title(title_tag.text)
        logger.debug("Тег <title> не найден")

        # 3. Заголовки h1, h2
        for tag in ["h1", "h2"]:
            logger.debug(f"Проверка тега {tag}")
            header = soup.select_one(tag)
            if header and header.text:
                logger.info(f"Название найдено в {tag}: {header.text}")
                return clean_title(header.text)
            logger.debug(f"Тег {tag} не найден")

        # 4. Классы
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

        # 5. JSON-LD
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

        logger.warning("Название не найдено через requests")
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

@app.get("/health")
async def health_check():
    """Проверка работоспособности API."""
    logger.info("Получен запрос на проверку работоспособности")
    return {"status": "healthy", "message": "API is running"}

@app.post("/extract-title", response_model=TitleResponse)
async def get_product_title(request: URLRequest):
    """API endpoint для извлечения названия по URL."""
    logger.info(f"Получен POST запрос на обработку URL: {request.url}")
    start_time = time.time()
    
    # Валидация URL
    if not request.url.startswith(("http://", "https://")):
        logger.error("Некорректный URL: отсутствует схема http(s)")
        raise HTTPException(status_code=400, detail="URL должен начинаться с http:// или https://")

    # Попробуем через requests
    logger.debug("Запуск метода requests")
    title = extract_title_requests(request.url)
    if title:
        logger.info(f"Успешно найдено название через requests: {title}")
        logger.debug(f"Общее время обработки: {time.time() - start_time:.2f} секунд")
        return {"url": request.url, "title": title}

    # Если requests не сработал, пробуем Selenium
    logger.debug("Переход к методу Selenium")
    driver = setup_selenium()
    if not driver:
        logger.error("Не удалось инициализировать Selenium")
        raise HTTPException(status_code=500, detail="Не удалось запустить Selenium")

    try:
        title = extract_title_selenium(driver, request.url)
        if title:
            logger.info(f"Успешно найдено название через Selenium: {title}")
            logger.debug(f"Общее время обработки: {time.time() - start_time:.2f} секунд")
            return {"url": request.url, "title": title}
        else:
            logger.warning("Название не найдено ни одним методом")
            logger.debug(f"Общее время обработки: {time.time() - start_time:.2f} секунд")
            return {"url": request.url, "title": None}
    except Exception as e:
        logger.error(f"Ошибка обработки запроса: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при извлечении названия: {str(e)}")
    finally:
        try:
            logger.debug("Закрытие Selenium WebDriver")
            driver.quit()
            logger.info("Selenium успешно закрыт")
        except:
            logger.error("Ошибка при закрытии Selenium", exc_info=True)

if __name__ == "__main__":
    import uvicorn
    logger.info("Запуск FastAPI сервера")
    uvicorn.run(app, host="0.0.0.0", port=8000)