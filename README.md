# PriceTracker

![Логотип или скриншот проекта, если есть](ссылка_на_изображение)  
**Хакатон: [Human Hack Pro (Мета Хакатон)]**  
**Команда: [mov eax, 4]**

## Описание проекта

PriceTracker — сервис для отслеживания цен на маркетплейсах (Ozon, AliExpress, Wildberries и других), сравнения аналогов товаров и получения уведомлений о скидках. Наша цель — помочь пользователям покупать товары по самым выгодным ценам, экономя время и деньги.

**Ключевые функции**:  
- Автоматическое определение маркетплейса по ссылке на товар.  
- Извлечение данных о товаре (цена, название, характеристики).  
- Сравнение цен на аналоги товаров с разных платформ.  
- Отслеживание динамики цен с построением графиков.  
- Уведомления о снижении цен или появлении скидок (email, Telegram, пуш).  

**Целевая аудитория**:  
Покупатели маркетплейсов, которые хотят находить лучшие предложения и не упускать скидки.

## Проблема и решение

**Проблема**:  
Пользователи тратят часы на мониторинг цен на маркетплейсах, сравнение аналогов и поиск скидок. Часто они упускают выгодные предложения из-за отсутствия удобного инструмента для автоматизации.

**Решение**:  
PriceTracker автоматизирует процесс отслеживания цен, анализирует аналоги и уведомляет пользователей о лучших предложениях через удобные каналы. Сервис предоставляет наглядные графики динамики цен и помогает принимать обоснованные решения о покупке.

## Технический стек

- **Backend**: Python, FastAPI, Celery, PostgreSQL  
- **Frontend**: React, Zustand, Radix/MUI  
- **Инструменты и сервисы**: BeautifulSoup/Selenium (парсинг), Telegram API, Firebase (пуш-уведомления), Docker  
- **Другое**: Prometheus (мониторинг), Chart.js (графики)

## Процесс выполнения
 
1. **Идея и планирование**:  
   - Проанализировали задачу и выдвинули гипотезы (см. ниже).  
   - Распределили роли: backend, frontend, парсинг, UI/UX.  
2. **Разработка**:  
   - Реализовали парсер для [указать маркетплейсы, например: Ozon, Wildberries].  
   - Настроили API для извлечения и хранения данных.  
   - Создали фронтенд с формой добавления товаров и графиками.  
   - Интегрировали уведомления через [указать каналы, например: Telegram].  
3. **Тестирование**:  
   - Протестировали парсинг на [количество] товаров.  
   - Проверили точность обновления цен и доставку уведомлений.  
   - Исправили баги, связанные с [указать проблемы, если были].  
4. **Итог**:  
   - [Что успели: например, рабочий прототип с парсингом Ozon и уведомлениями].  

**Гипотезы, которые мы проверяли**:  
- **Сбор данных**: Универсальный парсер с адаптерами для маркетплейсов обеспечит стабильный сбор данных.  
- **Цены**: Регулярное обновление цен (каждые 1-2 часа) сохранит актуальность данных.  
- **Уведомления**: Многоканальные уведомления (email, Telegram, пуш) повысят удобство.  
- **UI/UX**: Интуитивная форма добавления товаров сократит время взаимодействия до 30 секунд.  
- **Масштабируемость**: Микросервисная архитектура выдержит рост до 10 000 пользователей.  

**Ключевые вызовы**:  
- [Проблема 1, например: Блокировка парсера маркетплейсом — решили через ротацию User-Agent.]  
- [Проблема 2, например: Сложности с сопоставлением аналогов — использовали алгоритм текстового сходства.]  

**Что можно улучшить**:  
- Добавить поддержку новых маркетплейсов.  
- Улучшить алгоритм сравнения аналогов по характеристикам.  
- Оптимизировать производительность парсера.

## Демо

[Ссылка на видео, прототип или скриншоты. Например: "Скриншоты интерфейса в папке /screenshots".]  
**Инструкция для запуска**:  
