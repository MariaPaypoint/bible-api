# Bible API

REST API для работы с переводами Библии, озвучкой и аномалиями.

## Аномалии озвучки

### Статусы аномалий

- `detected` - ошибка выявлена автоматически (по умолчанию)
- `confirmed` - ошибка подтверждена при проверке  
- `disproved` - ошибка опровергнута, не подтверждена проверкой
- `corrected` - выполнена ручная коррекция
- `already_resolved` - уже исправлена ранее (только для системного использования)

### API методы

#### GET /voices/{voice_code}/anomalies

Получение списка аномалий для голоса с возможностью фильтрации по статусу.

**Параметры:**
- `voice_code` (path) - код голоса
- `status` (query, optional) - фильтр по статусу аномалии

**Пример запроса:**
```
GET /voices/1/anomalies?status=detected
```

#### PATCH /voices/anomalies/{anomaly_code}/status

Обновление статуса аномалии с возможностью корректировки временных меток.

**Параметры:**
- `anomaly_code` (path) - код аномалии

**Тело запроса:**
```json
{
  "status": "detected|confirmed|disproved|corrected",
  "begin": 10.5,  // только для статуса "corrected"
  "end": 12.0     // только для статуса "corrected"
}
```

**Правила валидации:**
- Для статуса `corrected` поля `begin` и `end` **обязательны**
- Для других статусов поля `begin` и `end` **недопустимы**
- `begin` должно быть меньше `end`
- Статус `already_resolved` нельзя устанавливать вручную
- **Нельзя изменить статус с `corrected` на `confirmed`**

**Примеры запросов:**

1. Подтверждение аномалии:
```json
{
  "status": "confirmed"
}
```

2. Опровержение аномалии:
```json
{
  "status": "disproved"
}
```

3. Коррекция с новыми временными метками:
```json
{
  "status": "corrected",
  "begin": 10.5,
  "end": 12.0
}
```

#### POST /voices/anomalies

Создание новой аномалии озвучки.

**Тело запроса:**
```json
{
  "voice": 1,
  "translation": 1,
  "book_number": 1,
  "chapter_number": 1,
  "verse_number": 1,
  "word": "слово",           // опционально
  "position_in_verse": 5,    // опционально
  "position_from_end": 3,    // опционально
  "duration": 1.5,           // опционально
  "speed": 2.0,              // опционально
  "ratio": 1.8,              // обязательно, должно быть > 0
  "anomaly_type": "manual",  // по умолчанию "manual"
  "status": "detected"       // по умолчанию "detected"
}
```

**Типы аномалий:**
- `fast` - быстрое произношение
- `slow` - медленное произношение  
- `long` - длинная пауза
- `short` - короткая пауза
- `manual` - добавлена вручную (по умолчанию)

**Правила валидации:**
- Поле `ratio` обязательно и должно быть положительным числом
- Поля `voice`, `translation`, `book_number`, `chapter_number`, `verse_number` обязательны
- Система проверяет существование указанного голоса, перевода и стиха
- Тип аномалии должен быть одним из допустимых значений

**Пример успешного ответа:**
```json
{
  "code": 123,
  "voice": 1,
  "translation": 1,
  "book_number": 1,
  "chapter_number": 1,
  "verse_number": 1,
  "word": "слово",
  "position_in_verse": 5,
  "position_from_end": 3,
  "duration": 1.5,
  "speed": 2.0,
  "ratio": 1.8,
  "anomaly_type": "manual",
  "status": "detected",
  "verse_start_time": 10.0,
  "verse_end_time": 12.0,
  "verse_text": "Текст стиха"
}
```

### Логика работы с voice_manual_fixes

При обновлении статуса аномалии система автоматически управляет таблицей `voice_manual_fixes`:

#### Статусы DISPROVED и CORRECTED
- Создается или обновляется запись в `voice_manual_fixes`
- Для `DISPROVED`: используются оригинальные временные метки из `voice_alignments`
- Для `CORRECTED`: используются переданные в запросе `begin` и `end`

#### Статус CONFIRMED
- Если есть запись в `voice_manual_fixes` с совпадающими временными метками - она удаляется
- Если временные метки не совпадают - возвращается ошибка 422
- Если записи нет - никаких действий не выполняется

Это позволяет отслеживать стихи, которые были вручную проверены, чтобы при перепарсинге не создавать для них новые аномалии.

## Отрывки с учетом корректировок

### GET /excerpt_with_alignment

Метод получения отрывков Библии с временными метками озвучки теперь автоматически учитывает корректировки из таблицы `voice_manual_fixes`.

**Логика работы:**
- Если для стиха есть запись в `voice_manual_fixes` - используются скорректированные временные метки
- Если записи нет - используются оригинальные временные метки из `voice_alignments`
- Реализовано через SQL COALESCE: `COALESCE(vmf.begin, a.begin)` и `COALESCE(vmf.end, a.end)`

**Пример запроса:**
```
GET /excerpt_with_alignment?translation=16&excerpt=jhn 3:16-17&voice=1
```

В ответе поля `begin` и `end` для каждого стиха будут содержать актуальные временные метки с учетом всех корректировок.

## Установка и запуск

### Установка зависимостей

```bash
# Установить основные зависимости
pip install mysql-connector-python fastapi uvicorn pydantic

# Для разработки (опционально, может потребовать Python 3.12 или ниже)
pip install pytest requests

# Полная установка (может не работать с Python 3.13)
# pip install -r requirements.txt
```

### Настройка базы данных

1. Скопируйте файл конфигурации:
```bash
cp app/config.sample.py app/config.py
```

2. Отредактируйте `app/config.py` с вашими настройками базы данных.

3. Выполните миграции:
```bash
python migrations/migration_manager.py migrate
```

**Примечание**: Миграции для рефакторинга `voice_alignments` уже выполнены:
- ✅ Добавлены поля `book_number`, `chapter_number`, `verse_number`
- ✅ Созданы индексы для оптимизации производительности
- ✅ Заполнены данные из связанных таблиц
- ✅ Обновлен код для использования новых полей

### Запуск сервера

#### Вариант 1: Через Docker (рекомендуется)
```bash
# Запуск в фоновом режиме
docker compose up -d

# Проверить статус
docker compose ps

# Просмотр логов
docker logs bible-api

# Остановить
docker compose down
```
Сервер будет доступен на: http://localhost:8000

#### Вариант 2: Локальный запуск
```bash
# Запуск в режиме разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```
Сервер будет доступен на: http://localhost:8001

#### Проверка работы
```bash
# Swagger UI (Docker)
curl http://localhost:8000/docs

# Swagger UI (локальный запуск)
curl http://localhost:8001/docs
```

### Запуск тестов

```bash
# Установить pytest если еще не установлен
pip install pytest

# Запустить тесты
PYTHONPATH=/root/cep/bible-api/app python -m pytest tests/ -v
```

## Миграции

Система использует собственный механизм миграций для управления схемой базы данных.

```bash
# Выполнить все ожидающие миграции
python migrations/migration_manager.py migrate

# Создать новую миграцию
python migrations/migration_manager.py create --name "migration_name"

# Показать статус миграций
python migrations/migration_manager.py status

# Откатить миграцию (только отметить как не выполненную)
python migrations/migration_manager.py rollback --file "migration_file.sql"

# Отметить миграцию как выполненную без запуска
python migrations/migration_manager.py mark-executed --file "migration_file.sql"
```

Подробнее см. [migrations/README.md](migrations/README.md)
