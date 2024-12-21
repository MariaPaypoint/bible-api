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
        FROM translations
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
    
def get_voice_info(cursor, voice: int, translation: int) -> dict:
    query = '''
        SELECT name, link_template
        FROM voices
        WHERE code = %s
          AND translation = %s
    '''
    cursor.execute(query, (voice, translation,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(
            status_code=422, 
            detail=f"Voice {voice} not found for translation {translation}."
        )
    
    return result

def get_book_number(cursor: int, book_alias: str) -> str:
    query = '''
        SELECT alias 
        FROM keywords 
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
    
    return result['alias']

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

# Модель для простого ответа с ошибкой
class SimpleErrorResponse(BaseModel):
    detail: str

@router.get('/excerpt_with_alignment', response_model=ExcerptWithAlignmentModel, operation_id="get_excerpt_with_alignment", responses={422: {"model": SimpleErrorResponse}})
async def get_excerpt_with_alignment(translation: int, excerpt: str, voice: Optional[int] = None):
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
            book_number = get_book_number(cursor, book_alias)
            book_name = get_book_name(cursor, translation, book_number)

            # Формирование SQL-запроса для получения данных из БД
            verses_query = '''
                SELECT 
                    v.code, v.verse_number, v.verse_number_join, v.html, v.text, v.start_paragraph, 
                    a.begin, a.end 
                FROM translation_verses AS v
                    LEFT JOIN voice_alignments a ON a.translation_verse = v.code AND voice = %(voice)s
                WHERE translation_book = (
                        SELECT code 
                        FROM translation_books 
                        WHERE translation=%(translation)s AND book_number=%(book_number)s
                    )
                    AND chapter_number = %(chapter_number)s
                ORDER BY v.verse_number
            '''
            params = {
                'voice': voice,
                'translation': translation,
                'book_number': book_number,
                'chapter_number': chapter_number,
            }
            if start_verse is not None:
                is_single_chapter = False
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

            verses = []
            for verse in verses_results:
                if verse['begin'] is None or verse['end'] is None:
                #    raise HTTPException(
                #        status_code=422, 
                #        detail=f"Verse alignment not found for verse {verse['verse_number']}"
                #    )
                    verse['begin'] = 0
                    verse['end'] = 0
                
                verse_model = VerseWithAlignmentModel(
                    code=verse['code'],
                    number=verse['verse_number'],
                    join=verse['verse_number_join'],
                    html=verse['html'],
                    text=verse['text'],
                    begin=verse['begin'],  # Мы уже проверили, что 'begin' не равен None
                    end=verse['end'] if verse['end'] is not None else 0.0,
                    start_paragraph=verse['start_paragraph']
                )
                verses.append(verse_model)

            audio_link = voice_info['link_template'] if voice_info else '' # https://4bbl.ru/data/syn-bondarenko/{book_zerofill}/{chapter_zerofill}.mp3
            audio_link = audio_link.format(
                book_zerofill=str(book_number).zfill(2), 
                chapter_zerofill=str(chapter_number).zfill(2),
                book=book_number,
                chapter=chapter_number,
                book_alias=book_alias
            ) if audio_link else ''

            codes = ", ".join(str(verse.code) for verse in verses)
            
            # примечания
            query = '''
                SELECT code, note_number, text, translation_verse, position_text, position_html
                FROM translation_notes
                WHERE translation_verse IN (%s)
            ''' % codes
            cursor.execute(query)
            notes_results = cursor.fetchall()
            notes = []
            for note in notes_results:
                note_model = NoteModel(
                    code=note['code'],
                    number=note['note_number'],
                    text=note['text'],
                    verse_code=note['translation_verse'],
                    position_text=note['position_text'],
                    position_html=note['position_html']
                )
                notes.append(note_model)

            # заголовки
            query = '''
                SELECT code, text, before_translation_verse
                FROM translation_titles
                WHERE before_translation_verse IN (%s)
            ''' % codes
            cursor.execute(query)
            titles_results = cursor.fetchall()
            titles = []
            for title in titles_results:
                title_model = TitleModel(
                    code=title['code'],
                    text=title['text'],
                    before_verse_code=title['before_translation_verse']
                )
                titles.append(title_model)

            part = PartsWithAlignmentModel(
                book_number=book_number,
                book_name=book_name,
                chapter_number=chapter_number,
                audio_link=audio_link,
                verses=verses,
                notes=notes,
                titles=titles
            )

            parts.append(part)
        
        if len(parts) == 1:
            title = f"{book_name} {chapter_number}"
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
