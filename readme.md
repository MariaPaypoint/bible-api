# Bible Api

Сервис для получения по api списков имеющихся переводов Библии, озвучек, а также текстов и информации по выравниванию аудио и текста (сопоставление каждого стиха с его временем в аудиозаписи).

Данные в БД попадают через этот парсер https://github.com/MariaPaypoint/bible-parser.

## Установка и запуск

### Локальная установка

1. Создайте виртуальную среду:
```bash
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте базу данных:
   - Скопируйте `app/config.sample.py` в `app/config.py`
   - Заполните настройки подключения к MySQL
   - Выполните миграции базы данных: `python migrate.py migrate`

4. Запустите сервер разработки:
```bash
# Способ 1: через fastapi CLI
fastapi dev app/main.py --port 8000 --host 0.0.0.0

# Способ 2: через uvicorn (если первый не работает)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

После запуска сервер будет доступен по адресу: http://localhost:8000

Документация API: http://localhost:8000/docs

**Устранение неполадок:**
- Если команда `fastapi` не найдена, убедитесь что виртуальная среда активирована
- Если не работает первый способ, используйте `uvicorn`
- Порт 8000 должен быть свободен

**Настройка доступа извне (Google Cloud):**

Если сервер работает локально, но не доступен по внешнему IP, нужно настроить firewall:

```bash
# Через gcloud CLI (после авторизации)
gcloud compute firewall-rules create allow-bible-api-8000 \
    --allow tcp:8000 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow Bible API on port 8000"
```

Или через веб-консоль:
1. Google Cloud Console → VPC network → Firewall
2. CREATE FIREWALL RULE
3. Name: `allow-bible-api-8000`
4. Direction: `Ingress`, Action: `Allow`
5. Source IP ranges: `0.0.0.0/0`
6. Protocols: `TCP`, Ports: `8000`

### Запуск через Docker
```bash
docker compose up -d
```

### Запуск тестов

```bash
# Убедитесь, что виртуальная среда активирована
source venv/bin/activate

# Запустите все тесты
PYTHONPATH=app python -m pytest tests/ -v

# Или запустите конкретный тест
PYTHONPATH=app python -m pytest tests/test_excerpt.py::test_excerpt_jhn_3_16_17 -v
```

## Управление миграциями базы данных

Проект использует систему миграций для управления схемой базы данных.

### Основные команды

```bash
# Выполнить все ожидающие миграции
python migrate.py migrate

# Создать новую миграцию
python migrate.py create "migration_name"

# Посмотреть статус миграций
python migrate.py status

# Откатить миграцию (только запись в таблице)
python migrate.py rollback "migration_file.sql"

# Пометить миграцию как выполненную (для существующих БД)
python migrate.py mark-executed "migration_file.sql"
```

### Создание миграций

При создании новой миграции:
1. Используйте описательное имя: `python migrate.py create "add_user_table"`
2. Отредактируйте созданный SQL-файл в папке `migrations/`
3. Каждое SQL-выражение должно заканчиваться точкой с запятой
4. Выполните миграцию: `python migrate.py migrate`

Подробнее см. `migrations/README.md`

## Development usefull commands

### Управление зависимостями

После установки какого-либо пакета - зафиксировать изменения:
```bash
pip freeze > requirements.txt
```

### Генерация OpenAPI спецификации

Генерация yaml-файла из json для генераторов кода клиентских приложений (таких как https://github.com/apple/swift-openapi-generator)
```bash
python extract-openapi.py --app-dir app main:app --out openapi_generated.yaml
```

или через docker:
```bash
docker exec -it bible-api python extract-openapi.py --app-dir app main:app --out openapi_generated.yaml
```

Подробнее [тут](https://www.doctave.com/blog/python-export-fastapi-openapi-spec).

### Тестирование

Запуск всех тестов:
```bash
PYTHONPATH=app python -m pytest tests/ -v
```

Запуск конкретного теста:
```bash
PYTHONPATH=app python -m pytest tests/test_excerpt.py::test_excerpt_jhn_3_16_17 -v
```

Запуск с покрытием кода:
```bash
PYTHONPATH=app python -m pytest tests/ --cov=app --cov-report=html
```

### Логи

Смотреть логи Docker контейнера:
```bash
docker logs -f bible-api
```