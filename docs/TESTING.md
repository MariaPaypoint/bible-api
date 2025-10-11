# Тестирование

## Запуск тестов

⚠️ **ВАЖНО:** Integration тесты используют реальную БД из `app/config.py`

```bash
# Установить pytest
pip install pytest

# ✅ Безопасно - только unit тесты (НЕ пишут в БД)
pytest tests/ -k "not integration" -v

# ⚠️ ОПАСНО - все тесты (integration тесты используют БД!)
pytest tests/ -v
```

## Типы тестов

### Unit тесты (безопасные)
- Используют моки (`@patch`)
- **НЕ пишут в БД**
- Примеры: `test_anomaly_correction.py`, `test_voice_manual_fixes.py`

### Integration тесты (используют БД)
- Делают реальные HTTP запросы
- Используют БД из `app/config.py`
- Примеры: `test_*_integration.py`

## Статистика

- **Unit тесты:** ~60 тестов (безопасны)
- **Integration тесты:** ~38 тестов (используют БД)
- **Всего:** 98 тестов

## Рекомендации

1. **Для разработки:** запускайте только unit тесты
2. **Для CI/CD:** создайте тестовую БД
3. **Для production:** НЕ запускайте integration тесты

## Создание тестовой БД

```sql
CREATE DATABASE bible_pause_test LIKE bible_pause;
INSERT bible_pause_test SELECT * FROM bible_pause;
```

```python
# app/config_test.py
DB_NAME = "bible_pause_test"
```

```bash
export TEST_MODE=1
pytest tests/ -v
```
