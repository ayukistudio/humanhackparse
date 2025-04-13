from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import appwrite
from appwrite.client import Client
from appwrite.services.databases import Databases
from datetime import datetime
import asyncio
import re
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Output to console
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI()

# Appwrite configuration
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

def get_selenium_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    return driver

def extract_price(url: str) -> Optional[float]:
    driver = get_selenium_driver()
    try:
        driver.get(url)
        
        # Wait for price element to be visible (timeout 10 seconds)
        wait = WebDriverWait(driver, 10)
        
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

        # Clean price string
        price = re.sub(r'[^\d]', '', price) if price else None
        if price:
            logger.info(f"Extracted price {price} for URL: {url}")
        return float(price) if price else None
    
    except Exception as e:
        logger.error(f"Error extracting price for URL {url}: {e}")
        return None
    finally:
        driver.quit()

async def update_price_periodically(url: str, user_id: str):
    while True:
        price = extract_price(url)
        if price:
            current_time = datetime.now()
            document = {
                'user_id': user_id,
                'url': url,
                'date': current_time.strftime('%Y-%m-%d'),
                'time': current_time.strftime('%H:%M:%S'),
                'price': price
            }
            try:
                databases.create_document(
                    database_id=DATABASE_ID,
                    collection_id=COLLECTION_ID,
                    document_id='unique()',
                    data=document
                )
                logger.info(f"Price updated for URL: {url}, user_id: {user_id}, price: {price}, time: {current_time}")
            except Exception as e:
                logger.error(f"Error saving to Appwrite for URL {url}, user_id: {user_id}: {e}")
        
        # Wait 30 seconds
        await asyncio.sleep(1  * 60 * 60)

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: Ensure collection has required attributes
    try:
        # Check if collection exists, create attributes if needed
        databases.get_collection(database_id=DATABASE_ID, collection_id=COLLECTION_ID)
        
        # Ensure attributes exist
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
        logger.info("Collection attributes verified for products-track")
    except Exception as e:
        logger.error(f"Error setting up collection attributes: {e}")

    yield
    # Shutdown logic
    logger.info("Shutting down...")

# Attach lifespan to app
app.lifespan = lifespan

@app.post("/track-price")
async def track_price(request: ProductRequest, background_tasks: BackgroundTasks):
    price = extract_price(request.url)
    if not price:
        logger.warning(f"Failed to extract price for URL: {request.url}")
        return {"error": "Could not extract price"}

    current_time = datetime.now()
    document = {
        'user_id': request.user_id,
        'url': request.url,
        'date': current_time.strftime('%Y-%m-%d'),
        'time': current_time.strftime('%H:%M:%S'),
        'price': price
    }

    try:
        databases.create_document(
            database_id=DATABASE_ID,
            collection_id=COLLECTION_ID,
            document_id='unique()',
            data=document
        )
        logger.info(f"Initial price saved for URL: {request.url}, user_id: {request.user_id}, price: {price}")
        
        # Start background task for periodic updates
        background_tasks.add_task(update_price_periodically, request.url, request.user_id)
        
        return {"message": "Price tracking started", "initial_price": price}
    except Exception as e:
        logger.error(f"Failed to save initial data for URL: {request.url}, user_id: {request.user_id}: {e}")
        return {"error": f"Failed to save data: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)