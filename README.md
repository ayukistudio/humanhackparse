# Sauce Tracker

**Хакатон: [Human Hack Pro (Мета Хакатон)]**  
**Сложность: [Junior]**  
**Кейс: [Система отслеживания и сравнения цена маркетплейсах]**  
**Команда: [mov eax, 4]**

## Описание проекта

Sauce Tracker — сервис для отслеживания цен на маркетплейсах (Ozon, СберМегаМаркет, Wildberries и других), сравнения аналогов товаров и получения уведомлений о скидках. Наша цель — помочь пользователям покупать товары по самым выгодным ценам, экономя время и деньги, с использованием фильтрации по цене и по разным маркетплейсам.

**Ключевые функции**:  
- Определение товара по любой ссылке(которая является валидной страницей товара).  
- Извлечение данных о товаре (цена, название, картинка).  
- Фильтрация цен с аналогами товаров с разных платформ.  
- Отслеживание динамики цен с построением графиков.  
- Уведомления о снижении цен или появлении скидок (email, Telegram).  

**Целевая аудитория**:  
Покупатели маркетплейсов, которые хотят находить лучшие предложения и не упускать скидки.

## Проблема и решение

**Проблема**:  
Пользователи тратят часы на мониторинг цен на маркетплейсах, сравнение аналогов и поиск скидок. Часто они упускают выгодные предложения из-за отсутствия удобного инструмента для автоматизации.

**Решение**:  
Sauce Tracker автоматизирует процесс отслеживания цен, анализирует аналоги и уведомляет пользователей о лучших предложениях через удобные каналы. Сервис предоставляет наглядные графики динамики цен и помогает принимать обоснованные решения о покупке.

## Технический стек

- **Backend**: Python, Selenium, BeautifulSoup, FastAPI
- **Frontend**: NuxtJs, TailWind CSS, ShadCN, Pinia, Vue-query, ECharts 
- **Инструменты и сервисы**: AppWrite (auth/db), Docker

## Процесс выполнения
 
1. **Идея и планирование**:  
   - Проанализировали задачу и выдвинули гипотезы (см. ниже).  
   - Распределили роли: backend, frontend, парсинг, UI/UX.  
2. **Разработка**:  
   - Реализовали парсер для [Ozon, Wildberries, СберМегаМаркет, частично Aliexpress и ЯндексМаркет].  
   - Настроили API для извлечения и хранения данных.  
   - Создали фронтенд с формой авторизации, поиска товара по ссылке, разделения товаров по маркетплейсам, фильтрации товаров по цене, сохранения товаров в профиле определенного пользователя, создания динамической страницы товара с заголовком, изображением и графиком изменения цены товара.  
   - Интегрировали уведомления через Telegram-бота.
     
  ![Поиск товара по ссылке](https://github.com/ayukistudio/humanhackparse/blob/b6b64cc80f6c3c2ecf85da7f728a174f638294e4/screenshots/view/scr1.png)
   *Поиск товара по ссылке*

   ![Поиск товара по ссылке](https://github.com/ayukistudio/humanhackparse/blob/b6b64cc80f6c3c2ecf85da7f728a174f638294e4/screenshots/view/scr3.png)
   *Результаты поиска*

   ![Отображение карточки товара](https://github.com/ayukistudio/humanhackparse/blob/b6b64cc80f6c3c2ecf85da7f728a174f638294e4/screenshots/view/scr5.png)
   *Отображение карточки товара*

   ![Уведомление в тг-боте](https://github.com/ayukistudio/humanhackparse/blob/6d408811f4513841c3ba2bf1e51b63a093ee60da/screenshots/view/scr9.jpg)

   *Уведомление о снижении цены на товар в Telegram-боте*

   
3. **Тестирование**:   
   - Исправили баги, связанные с обходом антибота, правильной валидацией json, типизацией.  
4. **Итог**:  
   - Рабочий прототип приложения с парсингом, фильтрацией, уведомлениями о изменении цены, анализом цены, сохранением товара в личном кабинете пользователя, с аутентификацией.  

**Гипотезы, которые мы проверяли**:  
- **Сбор данных**: Универсальный парсер с адаптерами для маркетплейсов обеспечит стабильный сбор данных.  
- **Цены**: Регулярное обновление цен (каждые 18 часов) сохранит актуальность данных.  
- **Уведомления**: Уведомления в Telegram повысят удобство.  
- **UI/UX**: Интуитивная форма добавления товаров сократит время взаимодействия до 30 секунд. 

**Ключевые вызовы**:  
- [Проблема 1: Блокировка парсера маркетплейсом — с помощью Selenium эмулировали действия пользователя (случайные клики, прокрутку, задержки), использовали ротацию прокси и случайные User-Agent, загружали динамический контент через WebDriverWait, добавляем логирование и перехват ошибок для стабильности.]  
- [Проблема 2: Сложности с сопоставлением аналогов — использовали алгоритм текстового сходства (анализ и поиск названия по загаловку).]
- [Проблема 3: Сложности с многопоточностью — использовали библиотеку multiprocessing и применяли WebDriverWait.]

**Что можно улучшить**:  
- Добавить поддержку новых маркетплейсов.  
- Улучшить алгоритм сравнения аналогов по характеристикам.  
- Оптимизировать производительность парсера.
