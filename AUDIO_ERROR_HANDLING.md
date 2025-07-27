# Обработка ошибок в Audio API

## Новый формат ошибки 404

При запросе несуществующего аудиофайла API теперь возвращает структурированную ошибку с альтернативным URL.

### Формат ответа

```json
{
  "detail": {
    "detail": "Audio file not found on server: /path/to/file.mp3",
    "alternative_url": "https://example.com/audio/syn/bondarenko/01/01.mp3"
  }
}
```

### Поля ответа

- `detail.detail` - описание ошибки с путем к локальному файлу
- `detail.alternative_url` - корректный URL для загрузки файла (может быть `null`)

## Пример использования

### JavaScript

```javascript
async function loadAudio(translation, voice, book, chapter) {
    const response = await fetch(`/audio/${translation}/${voice}/${book}/${chapter}.mp3`);
    
    if (response.status === 404) {
        const error = await response.json();
        
        if (error.detail.alternative_url) {
            console.log(`Файл не найден. Загружаем с: ${error.detail.alternative_url}`);
            return fetch(error.detail.alternative_url);
        }
    }
    
    return response;
}
```

### Python

```python
import requests

def download_audio(translation, voice, book, chapter):
    url = f"/audio/{translation}/{voice}/{book:02d}/{chapter:02d}.mp3"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            error_data = e.response.json()
            alt_url = error_data['detail'].get('alternative_url')
            
            if alt_url:
                print(f"Загружаем с альтернативного URL: {alt_url}")
                return requests.get(alt_url).content
        
        raise e
```

## Преимущества

1. **Структурированные данные** - легко парсить в коде
2. **Прямой доступ к URL** - не нужно извлекать из строки
3. **Fallback логика** - можно автоматически переключаться на альтернативный источник
4. **Диагностика** - видно точный путь к отсутствующему файлу на сервере
