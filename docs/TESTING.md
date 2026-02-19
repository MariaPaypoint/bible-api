# Тестирование

## Тестовая БД

Тесты работают с отдельной БД `cep_test`, чтобы не затрагивать production-данные.

### Первоначальная настройка

```bash
# Создать тестовую БД (один раз, или после изменения миграций/seed-данных)
docker exec bible-api python tests/setup_test_db.py
```

Скрипт `setup_test_db.py`:
1. Пересоздаёт БД `cep_test` (DROP + CREATE)
2. Применяет все миграции из `migrations/`
3. Загружает seed-данные из `tests/seed_test_data.sql`

### Запуск тестов

```bash
# Unit тесты (используют моки, быстрые)
docker exec bible-api pytest tests/ -k "not integration" -v

# Все тесты (unit + integration)
docker exec bible-api pytest tests/ -v

# Один файл
docker exec bible-api pytest tests/test_excerpt.py -v

# Один тест
docker exec bible-api pytest tests/test_excerpt.py::test_function_name -v
```

Тесты запускаются внутри контейнера `bible-api` — им нужны env-переменные (`API_KEY`, `JWT_SECRET_KEY` и т.д.).

## Как это работает

`tests/conftest.py` устанавливает `os.environ["DB_NAME"] = "cep_test"` **до** импорта app-модулей. Поэтому `app/config.py` при загрузке читает `DB_NAME=cep_test` и все подключения идут в тестовую БД.

JWT-токен для admin-эндпоинтов получается через `TestClient` (без необходимости запущенного сервера).

## Типы тестов

### Unit тесты (безопасные)
- Используют моки (`@patch`)
- НЕ делают реальных запросов к БД
- Примеры: `test_anomaly_correction.py`, `test_voice_manual_fixes.py`

### Integration тесты
- Используют `TestClient` + реальную тестовую БД `cep_test`
- Примеры: `test_*_integration.py`

## Seed-данные

Файл `tests/seed_test_data.sql` содержит минимальный набор данных:
- `bible_books` — все 66 книг
- `languages` — ru, en, uk
- `translations` — SYNO (code=1), BSB (code=16)
- `translation_books` — книги для этих переводов
- `translation_verses` — gen 1:1, jhn 3:16-17
- `voices` — голос Бондаренко (code=1)
- `voice_alignments` — таймкоды для seed-стихов
- `voice_anomalies` — 2 аномалии для тестов
- `bible_stat` — данные для gen 1, jhn 3

При добавлении новых тестов, которым нужны данные — добавьте записи в `seed_test_data.sql` и перезапустите `setup_test_db.py`.

## Статистика

- **Unit тесты:** 64
- **Integration тесты:** 37
- **Всего:** 101
