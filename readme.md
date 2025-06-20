# Bible Api

Сервис для получения по api списков имеющихся переводов Библии, озвучек, а также текстов и информации по выравниванию аудио и текста (сопоставление каждого стиха с его временем в аудиозаписи).

Данные в БД попадают через этот парсер https://github.com/MariaPaypoint/bible-parser.

# Run dev
```
source venv/bin/activate
pip install -r requirements.txt
fastapi dev app/main.py --port 8000 --host 0.0.0.0
```

или через docker:
```
docker compose up -d
```

# Development usefull commands

После установки какого-либо пакета - зафиксировать изменения:
```
pip freeze > requirements.txt
```

Генерация yaml-файла из json для генераторов кода клиентских приложений (таких как https://github.com/apple/swift-openapi-generator)
```
python extract-openapi.py --app-dir app main:app --out openapi_generated.yaml
```

или через docker:
```
docker exec -it bible-api python extract-openapi.py --app-dir app main:app --out openapi_generated.yaml
```

Подробнее [тут](https://www.doctave.com/blog/python-export-fastapi-openapi-spec).

Смотреть логи

```
docker logs -f bible-api
```