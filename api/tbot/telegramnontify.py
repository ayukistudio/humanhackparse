from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional
import urllib.parse
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(module)s:%(lineno)d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("price_alert.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Price Alert API")

BOT_TOKEN = "7618020293:AAHINb-E14iVQGH57ObNdWN7oRZiVcNmLFM"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

SENDER_EMAIL = "your_gmail@gmail.com"
SENDER_PASSWORD = "your_app_password"

class PriceAlertRequest(BaseModel):
    username: str
    old_price: float
    new_price: float
    url: str
    image: str
    userid: str 
    email: str 

class PriceAlertResponse(BaseModel):
    message: str
    telegram_message: Optional[str] = None
    email_message: Optional[str] = None

async def validate_image_url(image_url: str) -> bool:
    """Проверяет доступность URL изображения."""
    logger.debug(f"Проверка URL изображения: {image_url}")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.head(image_url, follow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                logger.error(f"URL {image_url} не является изображением: {content_type}")
                return False
            logger.debug(f"URL изображения валиден: {image_url}")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Ошибка проверки URL изображения {image_url}: {str(e)}")
            return False

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(httpx.ReadTimeout),
    before_sleep=lambda retry_state: logger.debug(f"Повторная попытка {retry_state.attempt_number} после таймаута")
)
async def send_to_telegram(chat_id: str, message: str, image_url: str):
    logger.debug(f"Отправка сообщения в Telegram для chat_id: {chat_id}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            photo_payload = {
                "chat_id": chat_id,
                "photo": image_url,
                "parse_mode": "MarkdownV2"
            }
            photo_response = await client.post(f"{TELEGRAM_API_URL}/sendPhoto", json=photo_payload)
            photo_response.raise_for_status()
            logger.debug("Изображение успешно отправлено")

            text_payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "MarkdownV2"
            }
            text_response = await client.post(f"{TELEGRAM_API_URL}/sendMessage", json=text_payload)
            text_response.raise_for_status()
            logger.info(f"Сообщение успешно отправлено в Telegram для chat_id: {chat_id}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Ошибка HTTP при отправке в Telegram: {e.response.status_code} - {e.response.text}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Ошибка Telegram API: {e.response.text}")
        except httpx.ReadTimeout as e:
            logger.error(f"Таймаут при отправке в Telegram: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Общая ошибка при отправке в Telegram: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Ошибка отправки в Telegram: {str(e)}")

async def send_to_email(recipient_email: str, request: PriceAlertRequest):
    logger.debug(f"Отправка email на {recipient_email}")
    try:
        email_subject = f"Price Drop Alert for {request.username}"
        email_message = (
            f"Dear {request.username},\n\n"
            f"Great news! The item you're tracking has dropped in price:\n"
            f"Old price: {request.old_price:,.2f}\n"
            f"New price: {request.new_price:,.2f}\n\n"
            f"Check it out here: {request.url}\n\n"
            f"Best,\nSauce Tracker Team"
        )
        
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = email_subject
        msg.attach(MIMEText(email_message, 'plain'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        
        logger.info(f"Email успешно отправлен на {recipient_email}")
        return email_message
    except Exception as e:
        logger.error(f"Ошибка отправки email на {recipient_email}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка отправки email: {str(e)}")

def format_telegram_message(request: PriceAlertRequest) -> str:
    """Формирует отформатированное сообщение для Telegram."""
    logger.debug(f"Формирование сообщения для username: {request.username}, url: {request.url}")
    
    def escape_markdown(text):
        chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in chars:
            text = text.replace(char, f'\\{char}')
        return text

    username = escape_markdown(request.username)
    
    old_price = f"{request.old_price:.2f}".replace('.', '\\.')
    new_price = f"{request.new_price:.2f}".replace('.', '\\.')
    url = request.url

    message = (
        f"*{username}*, спешим сообщить, что интересующий вас товар *подешевел\\!* 🎉\n"
        f"Успейте отследить все изменения с помощью *Sauce Tracker*\n\n"
        f"💸 *{old_price}* ➡️ *{new_price}*\n\n"
        f"[🔗 Ссылка на товар]({url})"
    )

    logger.debug(f"Сформированное сообщение:\n{message}")
    return message

@app.get("/health")
async def health_check():
    """Проверка работоспособности API."""
    logger.info("Получен запрос на проверку работоспособности")
    return {"status": "healthy", "message": "API is running"}

@app.post("/send-telegram-alert", response_model=PriceAlertResponse)
async def send_telegram_alert(request: PriceAlertRequest):
    """API endpoint для отправки уведомления о снижении цены в Telegram."""
    logger.info(f"Получен POST запрос на Telegram: username={request.username}, url={request.url}, userid={request.userid}")

    if not request.url.startswith(("http://", "https://")):
        logger.error("Некорректный URL: отсутствует схема http(s)")
        raise HTTPException(status_code=400, detail="URL должен начинаться с http:// или https://")
    
    if not request.image.startswith(("http://", "https://")):
        logger.error("Некорректный URL изображения: отсутствует схема http(s)")
        raise HTTPException(status_code=400, detail="URL изображения должен начинаться с http:// или https://")
    
    if request.old_price <= request.new_price:
        logger.warning(f"Новая цена ({request.new_price}) не меньше старой ({request.old_price})")
        raise HTTPException(status_code=400, detail="Новая цена должна быть меньше старой")
    
    if request.old_price < 0 or request.new_price < 0:
        logger.error("Цены не могут быть отрицательными")
        raise HTTPException(status_code=400, detail="Цены не могут быть отрицательными")

    if not await validate_image_url(request.image):
        logger.error(f"Невалидный или недоступный URL изображения: {request.image}")
        raise HTTPException(status_code=400, detail="Невалидный или недоступный URL изображения")

    try:
        telegram_message = format_telegram_message(request)
        logger.info(f"Сообщение успешно сформировано для username: {request.username}")
        
        await send_to_telegram(request.userid, telegram_message, request.image)
        
        return {
            "message": "Price alert sent to Telegram successfully",
            "telegram_message": telegram_message
        }
    except Exception as e:
        logger.error(f"Ошибка при отправке в Telegram: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке в Telegram: {str(e)}")

@app.post("/send-email-alert", response_model=PriceAlertResponse)
async def send_email_alert(request: PriceAlertRequest):
    logger.info(f"Получен POST запрос на email: username={request.username}, url={request.url}, email={request.email}")

    if not request.url.startswith(("http://", "https://")):
        logger.error("Некорректный URL: отсутствует схема http(s)")
        raise HTTPException(status_code=400, detail="URL должен начинаться с http:// или https://")
    
    if not request.image.startswith(("http://", "https://")):
        logger.error("Некорректный URL изображения: отсутствует схема http(s)")
        raise HTTPException(status_code=400, detail="URL изображения должен начинаться с http:// или https://")
    
    if request.old_price <= request.new_price:
        logger.warning(f"Новая цена ({request.new_price}) не меньше старой ({request.old_price})")
        raise HTTPException(status_code=400, detail="Новая цена должна быть меньше старой")
    
    if request.old_price < 0 or request.new_price < 0:
        logger.error("Цены не могут быть отрицательными")
        raise HTTPException(status_code=400, detail="Цены не могут быть отрицательными")
    
    if not "@" in request.email or not "." in request.email:
        logger.error(f"Некорректный email: {request.email}")
        raise HTTPException(status_code=400, detail="Некорректный формат email")
        
    if not await validate_image_url(request.image):
        logger.error(f"Невалидный или недоступный URL изображения: {request.image}")
        raise HTTPException(status_code=400, detail="Невалидный или недоступный URL изображения")

    try:
        email_message = await send_to_email(request.email, request)
        
        return {
            "message": "Price alert sent to email successfully",
            "email_message": email_message
        }
    except Exception as e:
        logger.error(f"Ошибка при отправке на email: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке на email: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Запуск FastAPI сервера на порту 8100")
    uvicorn.run(app, host="0.0.0.0", port=8100)
