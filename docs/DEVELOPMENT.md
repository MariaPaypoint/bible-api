# Разработка

## Быстрый старт

```bash
# Настройка runtime-переменных
cp .env.example .env
nano .env

# Запуск в Docker
docker compose up -d --build

# Swagger UI
open http://localhost:8084/docs
```

## Docker команды

```bash
# Запуск
docker compose up -d --build

# Логи
docker logs bible-api -f

# Перезапуск
docker compose restart

# Остановка
docker compose down
```

## Миграции

```bash
# Применить все миграции
python migrate.py migrate

# Создать новую миграцию
python migrate.py create "migration_name"

# Статус
python migrate.py status
```

См. подробнее: [../migrations/README.md](../migrations/README.md)

## OpenAPI спецификация

```bash
# Экспорт OpenAPI схемы (выполняется в контейнере)
docker exec bible-api bash -c "cd /code && PYTHONPATH=app python3 extract-openapi.py app.main:app"
```

Создаст файл `openapi.yaml` с полной спецификацией API.

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
└── config.py         # Конфигурация из переменных окружения
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
  - Статусы: `detected`, `confirmed`, `disproved`, `corrected`, `already_resolved`, `disproved_whisper`

### Служебные

- **`migrations`** - история миграций БД
