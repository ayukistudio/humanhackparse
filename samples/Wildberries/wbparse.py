import cloudscraper
import json
import time
import random

def get_product_data(nm_id, dest="12358476"):
    """
    Получает данные карточки товара с Wildberries по nm_id.
    nm_id: ID товара (например, 217353421)
    dest: ID региона (по умолчанию 12358476)
    """
    # URL для запроса данных карточки товара
    url = f"https://card.wb.ru/cards/v2/list?curr=rub&dest={dest}&lang=ru&nm={nm_id}"

    # Создаем экземпляр cloudscraper для обхода антибот-защиты
    scraper = cloudscraper.create_scraper()

    # Заголовки для имитации браузера
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx",
        "Connection": "keep-alive",
    }

    try:
        # Задержка для имитации человеческого поведения
        time.sleep(random.uniform(1, 3))

        # Выполняем GET-запрос
        response = scraper.get(url, headers=headers)

        # Проверяем статус ответа
        if response.status_code == 200:
            # Парсим JSON-ответ
            data = response.json()
            return data
        else:
            print(f"Ошибка: Статус код {response.status_code}")
            return None

    except Exception as e:
        print(f"Ошибка при запросе: {e}")
        return None

def parse_product_info(data):
    """
    Извлекает ключевую информацию из JSON-данных карточки товара.
    """
    if not data or "data" not in data or not data["data"]["products"]:
        print("Данные о товаре не найдены")
        return None

    product = data["data"]["products"][0]  # Берем первый товар из списка

    # Извлекаем поле price напрямую
    price_data = product.get("sizes", [])[0].get("price", {})
    
    # Формируем словарь цен (оставляем в копейках, как в вашем примере)
    price_info = {
        "basic": price_data.get("basic", None),
        "product": price_data.get("product", None),
        "total": price_data.get("total", None),
        "logistics": price_data.get("logistics", None),
        "return": price_data.get("return", None),
    }

    # Извлекаем все остальные поля
    product_info = {
        "state": data.get("state", None),
        "payloadVersion": data.get("payloadVersion", None),
        "sort": product.get("sort", None),
        "time1": product.get("time1", None),
        "time2": product.get("time2", None),
        "wh": product.get("wh", None),
        "dtype": product.get("dtype", None),
        "dist": product.get("dist", None),
        "id": product.get("id", None),
        "root": product.get("root", None),
        "kindId": product.get("kindId", None),
        "brand": product.get("brand", None),
        "brandId": product.get("brandId", None),
        "siteBrandId": product.get("siteBrandId", None),
        "colors": [color["name"] for color in product.get("colors", []) if color.get("name")],
        "subjectId": product.get("subjectId", None),
        "subjectParentId": product.get("subjectParentId", None),
        "name": product.get("name", None),
        "entity": product.get("entity", None),
        "matchId": product.get("matchId", None),
        "supplier": product.get("supplier", None),
        "supplierId": product.get("supplierId", None),
        "supplierRating": product.get("supplierRating", None),
        "supplierFlags": product.get("supplierFlags", None),
        "pics": product.get("pics", None),
        "rating": product.get("rating", None),
        "reviewRating": product.get("reviewRating", None),
        "nmReviewRating": product.get("nmReviewRating", None),
        "feedbacks": product.get("feedbacks", None),
        "nmFeedbacks": product.get("nmFeedbacks", None),
        "panelPromoId": product.get("panelPromoId", None),
        "promoTextCard": product.get("promoTextCard", None),
        "promoTextCat": product.get("promoTextCat", None),
        "volume": product.get("volume", None),
        "viewFlags": product.get("viewFlags", None),
        "sizes": [
            {
                "name": size.get("name", None),
                "origName": size.get("origName", None),
                "rank": size.get("rank", None),
                "optionId": size.get("optionId", None),
                "wh": size.get("wh", None),
                "time1": size.get("time1", None),
                "time2": size.get("time2", None),
                "dtype": size.get("dtype", None),
            }
            for size in product.get("sizes", [])
        ],
        "price": price_info,  # Используем исправленный словарь цен
        "saleConditions": product.get("saleConditions", None),
        "payload": product.get("payload", None),
        "totalQuantity": product.get("totalQuantity", None),
        "meta": {
            "tokens": product.get("meta", {}).get("tokens", [])
        },
    }

    return product_info

def main():
    # ID товара из ссылки
    nm_id = "207324839"  # Используем артикул из вашего примера

    # Получаем данные
    data = get_product_data(nm_id)

    if data:
        # Парсим данные
        product_info = parse_product_info(data)

        if product_info:
            # Выводим информацию
            print("Информация о товаре:")
            for key, value in product_info.items():
                print(f"{key}: {value}")
        else:
            print("Не удалось извлечь информацию о товаре")
    else:
        print("Не удалось получить данные")

if __name__ == "__main__":
    main()