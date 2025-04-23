import json
import logging
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

def setup_selenium(proxy=None):
    """Инициализация Selenium с опциональным прокси."""
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
    options.add_argument("--ignore-ssl-errors=true")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-webgl")
    options.add_argument("--disable-accelerated-2d-canvas")
    options.add_argument("--no-zygote")
    options.add_argument("--disable-quic")
    options.add_argument("--no-experiments")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-gpu-sandbox")
    options.add_argument("--disable-angle")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-out-of-process-rasterization")
    options.add_argument("--disable-gpu-compositing")
    options.add_argument("--disable-web-security")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       	"(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    if proxy:
        logger.info(f"Используется прокси: {proxy}")
        options.add_argument(f'--proxy-server={proxy}')
    else:
        logger.info("Прокси не используется")

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(window, 'chrome', { get: () => ({ runtime: {} }) });
            """
        })
        logger.info("Selenium успешно инициализирован")
        return driver
    except Exception as e:
        logger.error(f"Ошибка инициализации Selenium: {e}")
        return None

def scroll_to_bottom(driver, max_scroll_time=10):
    start_time = time.time()
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        while time.time() - start_time < max_scroll_time:
            driver.execute_script("window.scrollBy(0, 2000);")
            time.sleep(random.uniform(0.1, 0.2))
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        logger.debug("Страница полностью прокручена")
    except Exception as e:
        logger.error(f"Ошибка при прокрутке страницы: {e}")

def handle_popups(driver):
    try:
        popup_selectors = [
            "button[class*='close'], button[class*='decline'], button[class*='cancel']",
            "div[class*='geo'] button, div[class*='modal'] button",
            "button[class*='cookie'], button[class*='accept']"
        ]

        for selector in popup_selectors:
            try:
                WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                ).click()
                logger.debug(f"Закрыто всплывающее окно с селектором: {selector}")
                time.sleep(random.uniform(0.1, 0.2))
                return
            except:
                continue
    except Exception as e:
        logger.debug(f"Ошибка при обработке всплывающих окон: {e}")

def simulate_human_behavior(driver):
    try:
        actions = ActionChains(driver)
        for _ in range(random.randint(8, 12)):
            actions.move_by_offset(random.randint(-300, 300), random.randint(-300, 300)).perform()
            time.sleep(random.uniform(0.05, 0.1))
        driver.execute_script("window.scrollBy(0, " + str(random.randint(600, 1000)) + ");")
        time.sleep(random.uniform(0.1, 0.2))
        for _ in range(random.randint(3, 5)):
            actions.move_to_element_with_offset(driver.find_element(By.TAG_NAME, "body"), random.randint(200, 600), random.randint(200, 600)).click().perform()
            time.sleep(random.uniform(0.1, 0.2))
        logger.debug("Имитация человеческого поведения выполнена")
    except Exception as e:
        logger.debug(f"Ошибка при имитации поведения: {e}")

def scrape_sbermegamarket(query):
    """Скрапинг СберМегаМаркета."""
    driver = setup_selenium()
    if not driver:
        logger.error("Не удалось инициализировать драйвер Selenium")
        return []

    encoded_query = query.replace(" ", "%20")
    base_url = f"https://megamarket.ru/catalog/?q={encoded_query}"
    logger.info(f"Запуск скрапинга для запроса: {query}")

    products = []
    max_pages = 5
    current_page = 1
    start_time = time.time()
    max_duration = 60
    max_retries = 1

    while current_page <= max_pages:
        if time.time() - start_time >= max_duration:
            logger.info("Достигнут лимит времени, завершаем")
            break

        page_url = f"{base_url}&page={current_page}"
        logger.info(f"Скрапинг страницы {current_page}: {page_url}")

        for attempt in range(max_retries):
            try:
                driver.get(page_url)
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                simulate_human_behavior(driver)
                handle_popups(driver)
                break
            except TimeoutException:
                logger.error(f"Тайм-аут загрузки страницы {current_page}")
                current_page += 1
                break
            except WebDriverException as e:
                logger.error(f"Ошибка WebDriver на странице {current_page}: {e}")
                current_page += 1
                break

        for _ in range(8):
            scroll_to_bottom(driver, max_scroll_time=10)
            time.sleep(random.uniform(0.1, 0.2))

        try:
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script("return document.querySelectorAll('div[class*=\"catalog-item-regular\"]').length > 0")
            )
        except TimeoutException:
            logger.error(f"Карточки не найдены на странице {current_page}")
            current_page += 1
            continue

        product_tiles = driver.find_elements(By.CSS_SELECTOR, "div[class*='catalog-item-regular']")
        product_tiles = [tile for tile in product_tiles if tile.find_elements(By.CSS_SELECTOR, "a.ddl_product_link")]
        logger.info(f"Найдено {len(product_tiles)} карточек на странице {current_page}")

        for tile in product_tiles:
            if time.time() - start_time >= max_duration:
                break

            product = {"title": None, "price": None, "link": None, "image": None, "article": None}

            try:
                link_elem = tile.find_element(By.CSS_SELECTOR, "a.ddl_product_link")
                product["link"] = link_elem.get_attribute("href")
            except:
                logger.debug("Ссылка не найдена")
                continue

            try:
                article_id = link_elem.get_attribute("data-product-id")
                product["article"] = article_id if article_id and article_id.isdigit() else None
            except:
                logger.debug("Артикул не найден")

            try:
                title_elem = tile.find_element(By.CSS_SELECTOR, "meta[itemprop='name']")
                product["title"] = title_elem.get_attribute("content").strip()
            except:
                try:
                    title_elem = tile.find_element(By.CSS_SELECTOR, "a.catalog-item-regular-desktop__title-link")
                    product["title"] = title_elem.text.strip()
                except:
                    logger.debug("Название не найдено")
                    continue

            try:
                price_elem = tile.find_element(By.CSS_SELECTOR, "div.catalog-item-regular-desktop__price")
                price_text = price_elem.text.strip().replace("\u2009", "").replace("₽", "").replace(" ", "").strip()
                product["price"] = price_text
            except:
                logger.debug("Цена не найдена")
                continue

            try:
                img_elem = tile.find_element(By.CSS_SELECTOR, "meta[itemprop='image']")
                product["image"] = img_elem.get_attribute("content")
            except:
                try:
                    img_elem = tile.find_element(By.CSS_SELECTOR, "img.pui-img")
                    product["image"] = img_elem.get_attribute("src")
                except:
                    logger.debug("Изображение не найдено")

            if product["title"] and product["price"]:
                products.append(product)
                logger.info(f"Добавлен товар: {product['title']}, цена={product['price']}")
            else:
                logger.debug(f"Пропущен товар: title={product['title']}, price={product['price']}")

        try:
            next_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.pagination__item--next"))
            )
            next_button.click()
            current_page += 1
            time.sleep(random.uniform(1, 2))
        except:
            logger.info(f"Кнопка пагинации не найдена, переходим через URL к странице {current_page + 1}")
            current_page += 1
            continue

    try:
        driver.quit()
        logger.info("Драйвер Selenium закрыт")
    except:
        pass

    return products
