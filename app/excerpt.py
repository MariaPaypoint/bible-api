from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional
from database import create_connection
import re
from models import *

router = APIRouter()

def get_translation_name(cursor, translation: int) -> str:
    query = '''
        SELECT name
        FROM bible_translations
        WHERE code = %s
    '''
    cursor.execute(query, (translation,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(
            status_code=422, 
            detail=f"Translation {translation} not found."
        )
    
    return result['name']
    
def get_voice_name(cursor, voice: int, translation: int) -> str:
    query = '''
        SELECT name
        FROM audio_voices
        WHERE code = %s
          AND bible_translation = %s
    '''
    cursor.execute(query, (voice, translation,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(
            status_code=422, 
            detail=f"Voice {voice} not found for translation {translation}."
        )
    
    return result['name']

# Модель для простого ответа с ошибкой
class SimpleErrorResponse(BaseModel):
    detail: str

@router.get('/excerpt_with_alignment', response_model=ExcerptWithAlignmentModel, operation_id="get_excerpt_with_alignment", responses={422: {"model": SimpleErrorResponse}})
async def get_excerpt_with_alignment(translation: int, excerpt: str, voice: Optional[int] = None):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        translation_name = get_translation_name(cursor, translation)
        voice_name = get_voice_name(cursor, voice, translation) if voice else ''

        # Регулярное выражение для парсинга строки
        pattern = r'(?P<book>[a-z]+) (?P<chapter>\d+)(:(?P<start_verse>\d+)(?:-(?P<end_verse>\d+))?)?'
        
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
            query = '''
                SELECT alias 
                FROM keyword_values 
                WHERE name = %s
                  AND group_alias = "book"
            '''
            cursor.execute(query, (book_alias,))
            result = cursor.fetchone()
            
            if not result:
                raise HTTPException(
                    status_code=422, 
                    detail=f"Book '{book_alias}' not found."
                )
            
            book_number = result['alias']

            # Формирование SQL-запроса для получения данных из БД
            verses_query = '''
                SELECT 
                v.code, v.verse_number, v.text, v.start_paragraph, 
                a.begin, a.end 
                FROM bible_verses AS v
                    LEFT JOIN audio_alignments a ON a.bible_verse = v.code AND audio_voice = %(voice)s
                WHERE bible_book = (
                        SELECT code 
                        FROM bible_books 
                        WHERE bible_translation=%(translation)s AND book_number=%(book_number)s
                    )
                    AND chapter_number = %(chapter_number)s
            '''
            params = {
                'voice': voice,
                'translation': translation,
                'book_number': book_number,
                'chapter_number': chapter_number,
            }
            if start_verse is not None:
                params['start_verse'] = int(start_verse)
                params['end_verse'] = int(end_verse) if end_verse else int(start_verse)
                if start_verse == end_verse:
                    verses_query += '''
                        AND verse_number = %(start_verse)s
                    '''
                else:
                    verses_query += '''
                        AND verse_number BETWEEN %(start_verse)s AND %(end_verse)s
                    '''
            cursor.execute(verses_query, params)
            verses_results = cursor.fetchall()

            if not verses_results:
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

            verses = [
                VerseWithAlignmentModel(
                    code=verse['code'],
                    number=verse['verse_number'],
                    text=verse['text'],
                    begin=verse['begin'] if verse['begin'] is not None else 0.0,
                    end=verse['end'] if verse['end'] is not None else 0.0,
                    start_paragraph=verse['start_paragraph']
                )
                for verse in verses_results
            ]

            part = PartsWithAlignmentModel(
                book_number=book_number,
                chapter_number=chapter_number,
                verses=verses
            )

            parts.append(part)
        
        title = f"Excerpt {excerpt}"

        return ExcerptWithAlignmentModel(title=title, parts=parts)
    
    except HTTPException as e:
        raise e  # Позволяем HTTPException пробрасываться дальше с корректным кодом ошибки
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")  # Для любых непредвиденных ошибок
    finally:
        cursor.close()
        connection.close()