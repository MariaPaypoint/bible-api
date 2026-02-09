# Reverse Proxy и Порты (Docker Compose)

Этот документ объясняет, как в проекте работает схема с `web` (Nginx) и `bible-api` (FastAPI).

## 1. Какие порты открыты наружу

В `docker-compose.yml` наружу публикуется только контейнер `web`:

```yaml
services:
  web:
    ports:
      - "80:80"
```

Это означает:
- внешний порт сервера `80` принимает Nginx;
- FastAPI напрямую снаружи не доступен.

## 2. Почему `bible-api` не торчит в интернет

У `bible-api` используется `expose`, а не `ports`:

```yaml
services:
  bible-api:
    expose:
      - "8000"
```

Разница:
- `ports` = публикует порт на хост (доступ извне);
- `expose` = порт доступен только контейнерам внутри Docker-сети.

## 3. Как Nginx отправляет запросы в FastAPI

В `deploy/nginx/default.conf`:

```nginx
upstream bible_api_upstream {
    server bible-api:8000;
}
```

Nginx обращается к контейнеру `bible-api` по имени сервиса внутри Docker-сети.

## 4. Маршрутизация по хостам и путям

### Для `yourdomain.com`
- `/` и обычные страницы: отдаются как статический сайт (`/root/cep/site`);
- `/api/*`, `/docs`, `/openapi.json`, `/redoc`: проксируются в FastAPI.

### Для `api.yourdomain.com`
- весь трафик (`/`) проксируется в FastAPI.

## 5. Что это дает

- На корне `yourdomain.com` можно держать сайт.
- API изолирован и ходит через Nginx.
- Можно использовать отдельный API-домен `api.yourdomain.com`.

## 6. Как это выглядит в dev

В `docker-compose.dev.yml`:
- `bible-api` публикуется напрямую (`8000:8000`), чтобы удобно дебажить API;
- `web` отключен профилем `prod`.

## 7. Краткий поток запроса

1. Клиент стучится в `http://yourdomain.com` или `http://api.yourdomain.com`.
2. Запрос попадает в контейнер `web` (Nginx) на порту `80`.
3. Nginx либо:
   - отдает статический файл,
   - либо проксирует на `bible-api:8000`.
4. FastAPI обрабатывает API-запрос и возвращает ответ через Nginx клиенту.
