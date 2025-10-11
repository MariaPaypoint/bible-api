# Безопасность и авторизация

## Архитектура

API использует двухуровневую систему авторизации:

1. **API Key** (`X-API-Key`) - для публичных GET эндпоинтов
2. **JWT Token** (`Authorization: Bearer`) - для административных операций

## Защищенные эндпоинты

| Эндпоинт | Метод | Защита | Назначение |
|----------|-------|--------|------------|
| `/auth/login` | POST | - | Получение JWT токена |
| `/languages` | GET | API Key | Список языков |
| `/translations` | GET | API Key | Список переводов |
| `/translation_info` | GET | API Key | Информация о переводе |
| `/translations/{code}/books` | GET | API Key | Книги перевода |
| `/chapter_with_alignment` | GET | API Key | Глава с выравниванием |
| `/excerpt_with_alignment` | GET | API Key | Отрывок с выравниванием |
| `/audio/{path}.mp3` | GET | API Key* | Аудиофайлы |
| `/translations/{code}` | PUT | JWT | Обновить перевод |
| `/voices/{code}` | PUT | JWT | Обновить голос |
| `/voices/{code}/anomalies` | GET | JWT | Список аномалий |
| `/voices/anomalies` | POST | JWT | Создать аномалию |
| `/voices/anomalies/{code}/status` | PATCH | JWT | Обновить статус |
| `/voices/manual-fixes` | POST | JWT | Ручная корректировка |
| `/check_translation` | GET | JWT | Проверка перевода |
| `/check_voice` | GET | JWT | Проверка озвучки |

**\*** Аудио эндпоинт поддерживает API ключ как в заголовке `X-API-Key`, так и в query параметре `?api_key=...` (для совместимости с HTML `<audio>` элементом)

## Конфигурация

```python
# app/config.py
API_KEY = "your-api-key-here"
JWT_SECRET_KEY = "your-secret-key"  # openssl rand -hex 32
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "$2b$12$..."  # bcrypt хеш
```

### Генерация хеша пароля

```bash
python -c "import bcrypt; print(bcrypt.hashpw(b'your_password', bcrypt.gensalt()).decode('utf-8'))"
```

## Использование

### API Key (публичные эндпоинты)

```bash
# Через заголовок (рекомендуется)
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/translations

# Аудио через query параметр (для <audio> элемента)
curl "http://localhost:8000/audio/syn/bondarenko/01/01.mp3?api_key=your-api-key"
```

### JWT Token (административные эндпоинты)

```bash
# 1. Получить токен
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r .access_token)

# 2. Использовать токен
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/voices/1/anomalies
```

## Реализация

- **`app/auth.py`** - функции авторизации и зависимости FastAPI
- **`app/config.py`** - настройки безопасности
