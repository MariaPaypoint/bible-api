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
        SELECT name, link_template
        FROM voices
        WHERE code = %s
          AND translation = %s
          AND active=1
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

@router.get('/excerpt_with_alignment', response_model=ExcerptWithAlignmentModel, operation_id="get_excerpt_with_alignment", responses={422: {"model": SimpleErrorResponse}}, tags=["Excerpts"])
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
            books_info_list = get_books_info(cursor, translation, book_alias)
            if not books_info_list:
                raise HTTPException(
                    status_code=422, 
                    detail=f"Book with alias '{book_alias}' not found for translation {translation}."
                )
            book_info = books_info_list[0]
            #book_number = book_info['number'] # get_book_number(cursor, book_alias)
            #book_name = book_info['name'] # get_book_name(cursor, translation, book_number)

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
            '''
            params = {
                'voice': voice,
                'translation': translation,
                'book_number': book_info['number'],
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
            
            verses_query += '''
                ORDER BY v.verse_number
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

            # ссыка на медиафайл
            audio_link = voice_info['link_template'] if voice_info else '' 
            audio_link = audio_link.format(
                book_zerofill=str(book_info['number']).zfill(2), 
                chapter_zerofill=str(chapter_number).zfill(2),
                chapter_zerofill3=str(chapter_number).zfill(3),
                chapter_zerofill_ps3=str(chapter_number).zfill(3 if book_info['number'] == 19 else 2),
                book=book_info['number'],
                chapter=chapter_number,
                book_alias=book_alias,
                book_alias_upper=book_alias.upper(),
                book_code2=book_info['code2'] if book_info['code2'] else '',
                book_code3=book_info['code3'] if book_info['code3'] else '',
                book_code4=book_info['code4'] if book_info['code4'] else '',
                book_code5=book_info['code5'] if book_info['code5'] else '',
                book_code6=book_info['code6'] if book_info['code6'] else '',
                book_code7=book_info['code7'] if book_info['code7'] else '',
                book_code8=book_info['code8'] if book_info['code8'] else '',
                book_code9=book_info['code9'] if book_info['code9'] else '',
            ) if audio_link else ''

            codes = ", ".join(str(verse.code) for verse in verses)
            
            # заголовки
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

            # примечания для стихов и заголовков
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