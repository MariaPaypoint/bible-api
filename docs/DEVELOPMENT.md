# Разработка

## Быстрый старт

```bash
# Настройка конфигурации
cp app/config.sample.py app/config.py
nano app/config.py

# Запуск в Docker
docker compose up -d

# Swagger UI
open http://localhost:8000/docs
```

## Docker команды

```bash
# Запуск
docker compose up -d

# Логи
docker logs bible-api -f

# Перезапуск
docker compose restart

# Остановка
docker compose down

# Пересборка
docker compose build --no-cache
```

## Миграции

```bash
# Применить все миграции
python migrations/migration_manager.py migrate

# Статус
python migrations/migration_manager.py status
```

См. подробнее: [../migrations/README.md](../migrations/README.md)

## OpenAPI спецификация

```bash
# Экспорт OpenAPI схемы в JSON
PYTHONPATH=app python extract-openapi.py app.main:app
```

Создаст файл `openapi.json` с полной спецификацией API.

## Структура проекта

```
app/
├── main.py           # Основное приложение FastAPI
├── auth.py           # Авторизация (API Key, JWT)
├── excerpt.py        # Эндпоинты для глав и отрывков
├── audio.py          # Аудиофайлы (Range requests, fallback)
├── checks.py         # Проверки БД
├── models.py         # Pydantic модели
├── database.py       # Подключение к БД
└── config.py         # Конфигурация (не в git)
```

## Таблицы БД

### Переводы и тексты

- **`languages`** - языки Библии
- **`translations`** - переводы Библии
- **`translation_books`** - книги в переводе
- **`translation_verses`** - стихи с текстом
- **`bible_stat`** - эталонное количество стихов (для валидации)

### Озвучки и аудио

- **`voices`** - озвучки переводов
- **`voice_alignments`** - тайминги слов в озвучке (begin/end для каждого слова)
- **`voice_manual_fixes`** - ручные корректировки таймингов
  - Приоритет выше, чем `voice_alignments`
  - SQL: `COALESCE(vmf.begin, a.begin)`
- **`voice_anomalies`** - автоматически обнаруженные проблемы
  - Типы: `fast`, `slow`, `long`, `short`, `manual`
  - Статусы: `detected`, `confirmed`, `disproved`, `corrected`, `already_resolved`

### Служебные

- **`migrations`** - история миграций БД
