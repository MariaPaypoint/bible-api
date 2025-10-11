"""
Роутер для работы с аудиофайлами
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from pathlib import Path
from datetime import datetime
import os

from config import MP3_FILES_PATH, AUDIO_BASE_URL
from auth import RequireAPIKey, verify_api_key_query
from database import create_connection

router = APIRouter(prefix="/audio", tags=["Audio"])


def get_voice_link_template(translation_alias: str, voice_alias: str) -> str:
    """
    Получает link_template для голоса из базы данных
    
    Args:
        translation_alias: Алиас перевода (например: syn, rst, bsb)
        voice_alias: Алиас голоса (например: bondarenko, barry_hays)
        
    Returns:
        Шаблон ссылки на аудиофайл или пустую строку, если не найден
    """
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = '''
            SELECT v.link_template
            FROM voices v
            JOIN translations t ON v.translation = t.code
            WHERE v.alias = %s 
              AND t.alias = %s
              AND v.active = 1
              AND t.active = 1
        '''
        
        cursor.execute(query, (voice_alias, translation_alias))
        result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return result['link_template'] if result and result['link_template'] else ''
        
    except Exception:
        return ''


def format_audio_url(link_template: str, book: str, chapter: str) -> str:
    """
    Форматирует URL аудиофайла на основе шаблона
    
    Args:
        link_template: Шаблон ссылки
        book: Номер книги
        chapter: Номер главы
        
    Returns:
        Отформатированный URL
    """
    if not link_template:
        return ''
        
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Получаем информацию о книге
        book_query = '''
            SELECT number, code1, code2, code3
            FROM bible_books
            WHERE number = %s
        '''
        
        cursor.execute(book_query, (int(book),))
        book_info = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if not book_info:
            return ''
            
        # Форматируем URL по аналогии с excerpt.py
        formatted_url = link_template.format(
            book_zerofill=str(book_info['number']).zfill(2),
            chapter_zerofill=str(int(chapter)).zfill(2),
            chapter_zerofill3=str(int(chapter)).zfill(3),
            chapter_zerofill_ps3=str(int(chapter)).zfill(3 if book_info['number'] == 19 else 2),
            book=book_info['number'],
            chapter=int(chapter),
            book_alias=book_info['code1'],
            book_alias_upper=book_info['code1'].upper(),
            book_code2=book_info['code2'] if book_info['code2'] else '',
            book_code3=book_info['code3'] if book_info['code3'] else ''
        )
        
        return formatted_url
        
    except Exception:
        return ''


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


def create_range_response(file_path: Path, range_header: Optional[str], translation: str = '', voice: str = '', book: str = '', chapter: str = ''):
    """Создает Response с поддержкой Range requests"""
    if not file_path.exists() or not file_path.is_file():
        # Получаем корректный URL для файла
        link_template = get_voice_link_template(translation, voice)
        correct_url = format_audio_url(link_template, book, chapter)
        
        error_response = AudioFileNotFoundError(
            detail=f"Audio file not found on server: {file_path.absolute()}",
            alternative_url=correct_url if correct_url else None
        )
        
        raise HTTPException(status_code=404, detail=error_response.model_dump())
    
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
def get_audio_file(
    translation: str, 
    voice: str, 
    book: str, 
    chapter: str, 
    request: Request,
    api_key: Optional[str] = None
):
    """
    Возвращает mp3 файл с поддержкой HTTP Range requests для iOS/Android плееров
    
    Args:
        translation: Код перевода (например: syn, rst, bsb)
        voice: Код голоса (например: bondarenko, barry_hays)  
        book: Номер книги (например: 01, 19, 40)
        chapter: Номер главы (например: 01, 14, 150)
        request: HTTP запрос
        api_key: API ключ (query параметр или заголовок X-API-Key)
        
    Returns:
        Аудиофайл или его часть с корректными заголовками
    """
    # Обрабатываем OPTIONS запрос для CORS
    if request.method == "OPTIONS":
        return Response(
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "Range, Content-Type, If-Range, X-API-Key",
                "Accept-Ranges": "bytes"
            }
        )
    
    # Проверяем API ключ: сначала из query параметра, потом из заголовка
    if api_key:
        # API ключ передан как query параметр
        verify_api_key_query(api_key)
    else:
        # Проверяем заголовок X-API-Key
        header_key = request.headers.get('x-api-key')
        verify_api_key_query(header_key)
    
    # Валидируем и строим путь к файлу
    file_path = validate_audio_path(translation, voice, book, chapter)
    
    # Получаем Range заголовок
    range_header = request.headers.get('range')
    
    # Возвращаем ответ с поддержкой Range requests
    return create_range_response(file_path, range_header, translation, voice, book, chapter) 