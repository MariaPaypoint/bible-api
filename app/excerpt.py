from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional
from database import create_connection
import re
import os
from pathlib import Path
from config import MP3_FILES_PATH, AUDIO_BASE_URL
from models import *
from auth import RequireAPIKey

router = APIRouter()

def get_translation_name(cursor, translation: int) -> str:
    query = '''
        SELECT name
        FROM translations
        WHERE code = %s
          AND active=1
    '''
    cursor.execute(query, (translation,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(
            status_code=422, 
            detail=f"Translation {translation} not found."
        )
    
    return result['name']
    
def get_voice_info(cursor, voice: int, translation: int) -> dict:
    query = '''
        SELECT v.name, v.link_template, v.alias as voice_alias, t.alias as translation_alias
        FROM voices v
        JOIN translations t ON v.translation = t.code
        WHERE v.code = %s
          AND v.translation = %s
          AND v.active=1
          AND t.active=1
    '''
    cursor.execute(query, (voice, translation,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(
            status_code=422, 
            detail=f"Voice {voice} not found for translation {translation}."
        )
    
    return result


def check_audio_file_exists(translation_alias: str, voice_alias: str, book_number: int, chapter_number: int) -> bool:
    """
    Проверяет существование аудиофайла в папке audio
    
    Args:
        translation_alias: Алиас перевода (например: syn, rst, bsb)
        voice_alias: Алиас голоса (например: bondarenko, barry_hays)
        book_number: Номер книги
        chapter_number: Номер главы
        
    Returns:
        True если файл существует, False если нет
    """
    # Формируем путь к файлу аналогично validate_audio_path из audio.py
    book_str = str(book_number).zfill(2)
    chapter_str = str(chapter_number).zfill(2)
    
    file_path = Path(MP3_FILES_PATH) / translation_alias / voice_alias / "mp3" / book_str / f"{chapter_str}.mp3"
    
    return file_path.exists()


def get_book_number(cursor: int, book_alias: str) -> str:
    query = '''
        SELECT number 
        FROM bible_books 
        WHERE code1 = %s 
    '''
    cursor.execute(query, (book_alias,))
    result = cursor.fetchone()
    
    if not result:
        raise HTTPException(
            status_code=422, 
            detail=f"Book '{book_alias}' not found."
        )
    
    return str(result['number'])
def get_book_alias(cursor: int, book_number: str) -> str:
    query = '''
        SELECT code1
        FROM bible_books 
        WHERE number = %s
    '''
    cursor.execute(query, (book_number,))
    result = cursor.fetchone()
    
    if not result:
        raise HTTPException(
            status_code=422, 
            detail=f"Book '{book_number}' not found."
        )
    
    return result['code1']


def get_chapter_data(cursor, translation: int, book_info: dict, chapter_number: int, voice: Optional[int] = None, voice_info: Optional[dict] = None, start_verse: Optional[int] = None, end_verse: Optional[int] = None) -> dict:
    """
    Получает данные главы: стихи, заголовки, примечания, аудио-ссылку
    
    Args:
        cursor: Курсор базы данных
        translation: Код перевода
        book_info: Информация о книге (должна содержать 'number', 'name', 'alias', etc.)
        chapter_number: Номер главы
        voice: Код голоса (опционально)
        voice_info: Информация о голосе (опционально)
        start_verse: Начальный стих (опционально, для диапазонов)
        end_verse: Конечный стих (опционально, для диапазонов)
    
    Returns:
        dict: Словарь с данными главы
    """
    # Формирование SQL-запроса для получения стихов с учетом корректировок
    verses_query = '''
        SELECT 
            v.code, v.verse_number, v.verse_number_join, v.html, v.text, v.start_paragraph,
            COALESCE(vmf.begin, a.begin) as begin,
            COALESCE(vmf.end, a.end) as end
        FROM translation_verses AS v
            LEFT JOIN voice_alignments a ON (
                a.voice = %(voice)s AND 
                a.book_number = %(book_number)s AND 
                a.chapter_number = %(chapter_number)s AND 
                a.verse_number = v.verse_number
            )
            LEFT JOIN voice_manual_fixes vmf ON (
                vmf.voice = %(voice)s AND 
                vmf.book_number = %(book_number)s AND 
                vmf.chapter_number = %(chapter_number)s AND 
                vmf.verse_number = v.verse_number
            )
        WHERE translation_book = (
                SELECT code 
                FROM translation_books 
                WHERE translation=%(translation)s AND book_number=%(book_number)s
            )
            AND v.chapter_number = %(chapter_number)s
    '''
    
    params = {
        'voice': voice,
        'translation': translation,
        'book_number': book_info['number'],
        'chapter_number': chapter_number,
    }
    
    # Добавляем фильтрацию по диапазону стихов, если указано
    if start_verse is not None:
        params['start_verse'] = start_verse
        params['end_verse'] = end_verse if end_verse else start_verse
        if start_verse == end_verse:
            verses_query += '''
                AND v.verse_number = %(start_verse)s
            '''
        else:
            verses_query += '''
                AND v.verse_number BETWEEN %(start_verse)s AND %(end_verse)s
            '''
    
    verses_query += '''
        ORDER BY v.verse_number
    '''
    
    cursor.execute(verses_query, params)
    verses_results = cursor.fetchall()

    if not verses_results:
        raise HTTPException(
            status_code=422, 
            detail=f"No verses found for book {book_info['number']}, chapter {chapter_number}."
        )

    verses = []
    for verse in verses_results:
        if verse['begin'] is None or verse['end'] is None:
            verse['begin'] = 0
            verse['end'] = 0
        
        verse_model = VerseWithAlignmentModel(
            code=verse['code'],
            number=verse['verse_number'],
            join=verse['verse_number_join'],
            html=verse['html'],
            text=verse['text'],
            begin=verse['begin'],
            end=verse['end'] if verse['end'] is not None else 0.0,
            start_paragraph=verse['start_paragraph']
        )
        verses.append(verse_model)

    # Ссылка на медиафайл
    audio_link = ''
    if voice_info:
        # Проверяем, существует ли аудиофайл в папке audio
        if check_audio_file_exists(
            voice_info['translation_alias'], 
            voice_info['voice_alias'], 
            book_info['number'], 
            chapter_number
        ):
            # Если файл существует, формируем ссылку на внутренний эндпоинт
            book_str = str(book_info['number']).zfill(2)
            chapter_str = str(chapter_number).zfill(2)
            audio_link = f"{AUDIO_BASE_URL}/audio/{voice_info['translation_alias']}/{voice_info['voice_alias']}/{book_str}/{chapter_str}.mp3"

    codes = ", ".join(str(verse.code) for verse in verses)
    
    # Заголовки
    titles_query = '''
        SELECT code, text, before_translation_verse, metadata, reference
        FROM translation_titles
        WHERE before_translation_verse IN (%s)
    ''' % codes
    cursor.execute(titles_query)
    titles_results = cursor.fetchall()
    titles = []
    title_codes = []
    for title in titles_results:
        title_model = TitleModel(
            code=title['code'],
            text=title['text'],
            before_verse_code=title['before_translation_verse'],
            metadata=title['metadata'],
            reference=title['reference']
        )
        titles.append(title_model)
        title_codes.append(str(title['code']))

    # Примечания для стихов и заголовков
    notes_query = '''
        SELECT code, note_number, text, translation_verse, translation_title, position_text, position_html
        FROM translation_notes
        WHERE translation_verse IN (%s)
    ''' % codes
    
    if title_codes:
        title_codes_str = ", ".join(title_codes)
        notes_query += ''' OR translation_title IN (%s)''' % title_codes_str
    
    cursor.execute(notes_query)
    notes_results = cursor.fetchall()
    notes = []
    for note in notes_results:
        note_model = NoteModel(
            code=note['code'],
            number=note['note_number'],
            text=note['text'],
            verse_code=note['translation_verse'],
            title_code=note['translation_title'],
            position_text=note['position_text'],
            position_html=note['position_html']
        )
        notes.append(note_model)

    return {
        'verses': verses,
        'titles': titles,
        'notes': notes,
        'audio_link': audio_link
    }

"""
def get_book_name(cursor: int, translation: int, book_number: str) -> str:
    query = '''
        SELECT name 
        FROM translation_books 
        WHERE translation = %s
            AND book_number = %s
    '''
    cursor.execute(query, (translation,book_number))
    result = cursor.fetchone()
    
    if not result:
        raise HTTPException(
            status_code=422, 
            detail=f"Book '{book_number}' not found in translation '{translation}'."
        )
    
    return result['name']
"""

# Модель для простого ответа с ошибкой
class SimpleErrorResponse(BaseModel):
    detail: str

@router.get('/chapter_with_alignment', response_model=ExcerptWithAlignmentModel, operation_id="get_chapter_with_alignment", responses={422: {"model": SimpleErrorResponse}}, tags=["Excerpts"])
async def get_chapter_with_alignment(translation: int, book_number: int, chapter_number: int, voice: Optional[int] = None, api_key: bool = RequireAPIKey):
    """
    Получить главу с выравниванием по номеру книги и главы
    
    Args:
        translation: Код перевода
        book_number: Номер книги (1-66)
        chapter_number: Номер главы
        voice: Код голоса (опционально)
    
    Returns:
        ExcerptWithAlignmentModel: Данные главы с выравниванием
    """
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        # Валидация входных параметров
        if book_number < 1 or book_number > 66:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid book number ({book_number}). Must be between 1 and 66."
            )
        
        if chapter_number < 1:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid chapter number ({chapter_number}). Must be greater than 0."
            )
        
        translation_name = get_translation_name(cursor, translation)
        voice_info = get_voice_info(cursor, voice, translation) if voice else None

        # Получаем информацию о книге по номеру
        cursor.execute('''
            SELECT tb.code, tb.book_number AS number, tb.name, bb.code1 AS alias, bb.code2, bb.code3, bb.code4, bb.code5, bb.code6, bb.code7, bb.code8, bb.code9,
                   (SELECT count(distinct chapter_number) FROM translation_verses WHERE translation_book = tb.code) AS chapters_count
            FROM translation_books AS tb
            LEFT JOIN bible_books AS bb ON bb.number = tb.book_number
            WHERE tb.translation = %s AND tb.book_number = %s
        ''', (translation, book_number))
        
        book_info = cursor.fetchone()
        if not book_info:
            raise HTTPException(
                status_code=422, 
                detail=f"Book {book_number} not found for translation {translation}."
            )
        
        # Проверяем, что глава существует
        if chapter_number > book_info['chapters_count']:
            raise HTTPException(
                status_code=422,
                detail=f"Chapter {chapter_number} not found. Book {book_number} has only {book_info['chapters_count']} chapters."
            )

        # Получаем данные главы через общую функцию
        chapter_data = get_chapter_data(cursor, translation, book_info, chapter_number, voice, voice_info)

        part = PartsWithAlignmentModel(
            book=book_info,
            prev_excerpt=get_prev_excerpt(cursor, translation, book_info, chapter_number),
            next_excerpt=get_next_excerpt(cursor, translation, book_info, chapter_number),
            chapter_number=chapter_number,
            audio_link=chapter_data['audio_link'],
            verses=chapter_data['verses'],
            notes=chapter_data['notes'],
            titles=chapter_data['titles']
        )

        title = f"{book_info['name']} {chapter_number}"

        return ExcerptWithAlignmentModel(
            title=title, 
            is_single_chapter=True,
            parts=[part]
        )
    
    except HTTPException as e:
        raise e
    finally:
        cursor.close()
        connection.close()


@router.get('/excerpt_with_alignment', response_model=ExcerptWithAlignmentModel, operation_id="get_excerpt_with_alignment", responses={422: {"model": SimpleErrorResponse}}, tags=["Excerpts"])
async def get_excerpt_with_alignment(translation: int, excerpt: str, voice: Optional[int] = None, api_key: bool = RequireAPIKey):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        translation_name = get_translation_name(cursor, translation)
        voice_info = get_voice_info(cursor, voice, translation) if voice else None

        is_single_chapter = True
        book_name = ''

        # Регулярное выражение для парсинга строки
        pattern = r'(?P<book>[0-9a-z]+) (?P<chapter>\d+)(:(?P<start_verse>\d+)(?:-(?P<end_verse>\d+))?)?'
        
        matches = list(re.finditer(pattern, excerpt))
        
        if not matches:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid excerpt format ({excerpt})."
            )

        parts = []

        for match in matches:
            book_alias = match.group('book')
            chapter_number = int(match.group('chapter'))
            start_verse = match.group('start_verse')
            end_verse = match.group('end_verse')

            # Получение кода книги на основе alias
            books_info_list = get_books_info(cursor, translation, book_alias)
            if not books_info_list:
                raise HTTPException(
                    status_code=422, 
                    detail=f"Book with alias '{book_alias}' not found for translation {translation}."
                )
            book_info = books_info_list[0]
            #book_number = book_info['number'] # get_book_number(cursor, book_alias)
            #book_name = book_info['name'] # get_book_name(cursor, translation, book_number)

            # Обработка диапазонов стихов
            if start_verse is not None:
                is_single_chapter = False
                start_verse_int = int(start_verse)
                end_verse_int = int(end_verse) if end_verse else start_verse_int
            else:
                start_verse_int = None
                end_verse_int = None

            # Получаем данные главы через общую функцию
            try:
                chapter_data = get_chapter_data(cursor, translation, book_info, chapter_number, voice, voice_info, start_verse_int, end_verse_int)
                verses = chapter_data['verses']
                titles = chapter_data['titles']
                notes = chapter_data['notes']
                audio_link = chapter_data['audio_link']
            except HTTPException as e:
                # Перехватываем и адаптируем сообщения об ошибках для excerpt формата
                if start_verse is None:
                    raise HTTPException(
                        status_code=422, 
                        detail=f"No verses found for {book_alias} {chapter_number}."
                    )
                else:
                    verse_range = f"{start_verse}" if start_verse == end_verse or end_verse is None else f"{start_verse}-{end_verse}"
                    raise HTTPException(
                        status_code=422, 
                        detail=f"No verses found for {book_alias} {chapter_number}:{verse_range}."
                    )

            part = PartsWithAlignmentModel(
                book=book_info,
                prev_excerpt=get_prev_excerpt(cursor, translation, book_info, chapter_number),
                next_excerpt=get_next_excerpt(cursor, translation, book_info, chapter_number),
                chapter_number=chapter_number,
                audio_link=audio_link,
                verses=verses,
                notes=notes,
                titles=titles
            )

            parts.append(part)
        
        if len(parts) == 1:
            title = f"{book_info['name']} {chapter_number}"
        elif len(parts) > 1:
            is_single_chapter = False
            title = f"Excerpt {excerpt}"
        else:
            title = ''

        return ExcerptWithAlignmentModel(
            title=title, 
            is_single_chapter=is_single_chapter,
            parts=parts
        )
    
    except HTTPException as e:
        raise e  # Позволяем HTTPException пробрасываться дальше с корректным кодом ошибки
    #except Exception as e:
    #    raise HTTPException(status_code=500, detail="Internal Server Error")  # Для любых непредвиденных ошибок
    finally:
        cursor.close()
        connection.close()


def get_books_info(cursor: any, translation: int, alias: str=None):
    params = { 'translation': translation }
    sql = '''
        SELECT 
            tb.code, tb.book_number AS number, tb.name, bb.code1 AS alias, bb.code2, bb.code3, bb.code4, bb.code5, bb.code6, bb.code7, bb.code8, bb.code9,
            (SELECT count(distinct chapter_number) FROM translation_verses WHERE translation_book = tb.code) AS chapters_count
        FROM translation_books AS tb
        LEFT JOIN bible_books AS bb ON bb.number = tb.book_number
        WHERE tb.translation = %(translation)s
    '''
    if alias:
        sql += ''' AND (bb.code1 = %(alias)s OR bb.code2 = %(alias)s OR bb.code3 = %(alias)s OR bb.code4 = %(alias)s OR bb.code5 = %(alias)s
                      OR bb.short_name_en = %(alias)s OR bb.short_name_ru = %(alias)s)
        '''
        params['alias'] = alias
    cursor.execute(sql, params)
    return cursor.fetchall()

def get_prev_excerpt(cursor: any, translation: int, book: BookInfoModel, chapter_number: int):
    if chapter_number > 1:
        return "%s %s" % (book['alias'], chapter_number-1)
    else:
        current_book_number = int(get_book_number(cursor, book['alias']))
        if current_book_number == 1:
            return '' # это первая книга первой главы
        else:
            prev_book_alias = get_book_alias(cursor, current_book_number-1)
            prev_book_info_list = get_books_info(cursor, translation, prev_book_alias)
            if prev_book_info_list:
                prev_book_info = prev_book_info_list[0]
                return "%s %s" % (prev_book_alias, prev_book_info['chapters_count'])
            else:
                return '' # предыдущая книга не найдена

    return ''

def get_next_excerpt(cursor: any, translation: int, book: BookInfoModel, chapter_number: int): 
    if chapter_number < book['chapters_count']:
        return "%s %s" % (book['alias'], chapter_number+1)
    else:
        current_book_number = int(get_book_number(cursor, book['alias']))
        if current_book_number == 66:
            return '' # это последняя книга последней главы
        else:
            next_book_alias = get_book_alias(cursor, current_book_number+1)
            # Проверяем, что следующая книга существует
            if next_book_alias:
                return "%s 1" % next_book_alias
            else:
                return '' # следующая книга не найдена

    return ''