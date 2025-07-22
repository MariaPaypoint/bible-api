"""
Роутер для работы с аудиофайлами
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from config import MP3_FILES_PATH

# Создаем роутер
router = APIRouter(prefix="/audio", tags=["Audio"])


def parse_range_header(range_header: str, file_size: int):
    """Парсит Range заголовок и возвращает start, end позиции"""
    if not range_header.startswith('bytes='):
        return None, None
    
    try:
        range_spec = range_header[6:]  # убираем 'bytes='
        if ',' in range_spec:
            # Берем только первый диапазон для простоты
            range_spec = range_spec.split(',')[0]
        
        if '-' not in range_spec:
            return None, None
            
        start_str, end_str = range_spec.split('-', 1)
        
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1
        
        # Убеждаемся что значения корректные
        start = max(0, start)
        end = min(file_size - 1, end)
        
        if start <= end:
            return start, end
        else:
            return None, None
            
    except (ValueError, IndexError):
        return None, None


def create_range_response(file_path: Path, range_header: Optional[str]):
    """Создает Response с поддержкой Range requests"""
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found: " + str(file_path.absolute()))
    
    file_size = file_path.stat().st_size
    file_stat = file_path.stat()
    
    # Базовые заголовки
    base_headers = {
        "Accept-Ranges": "bytes",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "max-age=432000",  # 5 дней
        "Connection": "keep-alive",
        "Last-Modified": datetime.fromtimestamp(file_stat.st_mtime).strftime('%a, %d %b %Y %H:%M:%S GMT'),
        "ETag": f'"{hex(hash(f"{file_stat.st_mtime}-{file_size}"))}"'
    }
    
    # Если нет Range заголовка, возвращаем весь файл
    if not range_header:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        base_headers["Content-Length"] = str(file_size)
        
        return Response(
            content=content,
            media_type="audio/mpeg",
            headers=base_headers
        )
    
    # Парсим Range заголовок
    start, end = parse_range_header(range_header, file_size)
    
    if start is None or end is None:
        # Невалидный Range, возвращаем 416
        return Response(
            status_code=416,
            headers={
                "Content-Range": f"bytes */{file_size}",
                "Accept-Ranges": "bytes"
            }
        )
    
    # Читаем нужную часть файла
    content_length = end - start + 1
    
    with open(file_path, 'rb') as f:
        f.seek(start)
        content = f.read(content_length)
    
    # Добавляем заголовки для partial content
    range_headers = base_headers.copy()
    range_headers.update({
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Content-Length": str(content_length)
    })
    
    return Response(
        content=content,
        status_code=206,
        media_type="audio/mpeg",
        headers=range_headers
    )


def validate_audio_path(translation: str, voice: str, book: str, chapter: str) -> Path:
    """
    Валидирует параметры и строит безопасный путь к файлу
    
    Args:
        translation: Код перевода
        voice: Код голоса  
        book: Номер книги
        chapter: Номер главы
        
    Returns:
        Путь к файлу
        
    Raises:
        HTTPException: При обнаружении небезопасных символов
    """
    # Проверяем на небезопасные символы
    for param_name, param_value in [
        ("translation", translation), 
        ("voice", voice), 
        ("book", book), 
        ("chapter", chapter)
    ]:
        if '..' in param_value or '/' in param_value or '\\' in param_value:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid {param_name} parameter: contains unsafe characters"
            )
    
    return Path(MP3_FILES_PATH) / translation / voice / "mp3" / book / f"{chapter}.mp3"


@router.get("/{translation}/{voice}/{book}/{chapter}.mp3", tags=["Audio"])
@router.head("/{translation}/{voice}/{book}/{chapter}.mp3", tags=["Audio"])
@router.options("/{translation}/{voice}/{book}/{chapter}.mp3", tags=["Audio"])
def get_audio_file(translation: str, voice: str, book: str, chapter: str, request: Request):
    """
    Возвращает mp3 файл с поддержкой HTTP Range requests для iOS/Android плееров
    
    Args:
        translation: Код перевода (например: syn, rst, bsb)
        voice: Код голоса (например: bondarenko, barry_hays)  
        book: Номер книги (например: 01, 19, 40)
        chapter: Номер главы (например: 01, 14, 150)
        request: HTTP запрос
        
    Returns:
        Аудиофайл или его часть с корректными заголовками
    """
    # Обрабатываем OPTIONS запрос для CORS
    if request.method == "OPTIONS":
        return Response(
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "Range, Content-Type, If-Range",
                "Accept-Ranges": "bytes"
            }
        )
    
    # Валидируем и строим путь к файлу
    file_path = validate_audio_path(translation, voice, book, chapter)
    
    # Получаем Range заголовок
    range_header = request.headers.get('range')
    
    # Возвращаем ответ с поддержкой Range requests
    return create_range_response(file_path, range_header) 