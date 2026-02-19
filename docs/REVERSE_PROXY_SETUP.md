# Reverse Proxy (опционально)

По умолчанию `bible-api` доступен напрямую на порту `8084` (хост) → `8000` (контейнер).

При необходимости перед API можно поставить Nginx reverse proxy.

## Пример конфигурации Nginx

Файл `deploy/nginx/default.conf` содержит пример конфигурации с:
- Проксированием `/api/*`, `/docs`, `/openapi.json`, `/redoc` в FastAPI
- Статическим сайтом на корне домена
- Поддержкой отдельного API-домена (`api.yourdomain.com`)

## Схема с reverse proxy

```
Клиент → Nginx (:80) → bible-api (:8000)
```

- Nginx обращается к контейнеру `bible-api` по имени сервиса внутри Docker-сети
- FastAPI напрямую снаружи недоступен (используется `expose` вместо `ports`)

## Схема без reverse proxy (текущая)

```
Клиент → bible-api (:8084 → :8000)
```

В текущем `docker-compose.yml` используется прямой маппинг портов без Nginx.
