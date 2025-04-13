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

# Configure logging
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

# FastAPI app
app = FastAPI(title="Price Alert API")

# Telegram Bot configuration
BOT_TOKEN = "7618020293:AAHINb-E14iVQGH57ObNdWN7oRZiVcNmLFM"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Gmail configuration
# 1. Включи двухфакторную аутентификацию в Google: https://myaccount.google.com/security
# 2. Перейди в "Пароли приложений": https://myaccount.google.com/security -> "App passwords"
# 3. Выбери "Mail" и "Other", введи имя (например, "PriceAlert"), получи 16-значный пароль (например, abcd efgh ijkl mnop)
# 4. Вставь свой Gmail и пароль приложения ниже (пароль без пробелов)
SENDER_EMAIL = "your_gmail@gmail.com"  # Замени на свой Gmail
SENDER_PASSWORD = "your_app_password"  # Замени на пароль приложения (16 символов без пробелов)

class PriceAlertRequest(BaseModel):
    username: str
    old_price: float
    new_price: float
    url: str
    image: str
    userid: str  # Telegram chat_id
    email: str   # Email получателя

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
    """Отправляет сообщение с изображением в Telegram с повторными попытками."""
    logger.debug(f"Отправка сообщения в Telegram для chat_id: {chat_id}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Сначала отправляем изображение
            photo_payload = {
                "chat_id": chat_id,
                "photo": image_url,
                "parse_mode": "MarkdownV2"
            }
            photo_response = await client.post(f"{TELEGRAM_API_URL}/sendPhoto", json=photo_payload)
            photo_response.raise_for_status()
            logger.debug("Изображение успешно отправлено")

            # Затем отправляем текстовое сообщение
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
    """Отправляет уведомление на почту через Gmail SMTP."""
    logger.debug(f"Отправка email на {recipient_email}")
    try:
        # Формирование сообщения для email
        email_subject = f"Price Drop Alert for {request.username}"
        email_message = (
            f"Dear {request.username},\n\n"
            f"Great news! The item you're tracking has dropped in price:\n"
            f"Old price: {request.old_price:,.2f}\n"
            f"New price: {request.new_price:,.2f}\n\n"
            f"Check it out here: {request.url}\n\n"
            f"Best,\nSauce Tracker Team"
        )

        # Настройка сообщения
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = email_subject
        msg.attach(MIMEText(email_message, 'plain'))

        # Подключение к Gmail SMTP
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
    
    # Экранирование специальных символов для Markdown V2
    def escape_markdown(text):
        chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in chars:
            text = text.replace(char, f'\\{char}')
        return text

    username = escape_markdown(request.username)
    # Форматируем цены без запятых, чтобы избежать проблем с экранированием
    old_price = f"{request.old_price:.2f}".replace('.', '\\.')
    new_price = f"{request.new_price:.2f}".replace('.', '\\.')
    url = request.url

    # Формирование сообщения в Markdown V2
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

    # Валидация данных
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

    # Проверка URL изображения
    if not await validate_image_url(request.image):
        logger.error(f"Невалидный или недоступный URL изображения: {request.image}")
        raise HTTPException(status_code=400, detail="Невалидный или недоступный URL изображения")

    # Формирование и отправка сообщения в Telegram
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
    """API endpoint для отправки уведомления о снижении цены на почту."""
    logger.info(f"Получен POST запрос на email: username={request.username}, url={request.url}, email={request.email}")

    # Валидация данных
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

    # Проверка URL изображения
    if not await validate_image_url(request.image):
        logger.error(f"Невалидный или недоступный URL изображения: {request.image}")
        raise HTTPException(status_code=400, detail="Невалидный или недоступный URL изображения")

    # Отправка на почту
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