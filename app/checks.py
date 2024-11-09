from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional
from database import create_connection
from models import *

router = APIRouter()

MUST_VERSES_COUNT = 31240

@router.get('/check_translation', operation_id="check_translation")
def check_translation(translation: Optional[int]):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        # проверка пустых стихов
        sql = '''
            SELECT tb.code AS book_code, tb.book_number, tb.name AS book_name, chapter_number, count(*) AS empty_verses_count
            FROM translation_verses AS v
              LEFT JOIN translation_books AS tb ON tb.code = v.translation_book AND tb.translation = %(translation)s
            WHERE text = ""
              AND tb.book_number IS NOT NULL
              AND verse_number_join >= 0
            GROUP BY tb.code, tb.book_number, tb.name, chapter_number
        '''
        cursor.execute(sql, {
            'translation': translation
        })
        result = cursor.fetchall()
        if result:
            raise HTTPException(status_code=422, detail={"error_description": "Empty verses", "error_list": result})
    
        # проверка количества стихов по главам
        sql = '''
			SELECT count(*) AS cc
			FROM translation_verses
            WHERE translation_book IN (
                SELECT code 
                FROM translation_books
                WHERE translation = %(translation)s
            )
		'''
        cursor.execute(sql, {
            'translation': translation
        })
        result = cursor.fetchall()
        verses_count = result[0]['cc']
        if verses_count != MUST_VERSES_COUNT:
            sql = '''
                SELECT s.book_number, s.chapter_number, s.verses_count AS must_verses_count, CONVERT(COUNT(tv.code) + IFNULL(SUM(tv.verse_number_join),0), SIGNED) AS translation_verses_count, s.tolerance_count
                FROM bible_stat AS s
                  LEFT JOIN translation_books AS tb ON tb.book_number = s.book_number AND tb.translation = %(translation)s
                  LEFT JOIN translation_verses AS tv ON tv.translation_book = tb.code AND tv.chapter_number = s.chapter_number
                WHERE s.book_number != 19 #psalms
                GROUP BY s.book_number, s.chapter_number, s.verses_count, s.tolerance_count
                HAVING ABS(must_verses_count - translation_verses_count) > tolerance_count
                ORDER BY book_number, chapter_number
            '''
            cursor.execute(sql, {
                'translation': translation
            })
            result = cursor.fetchall()
            if result:
                raise HTTPException(status_code=422, detail={"error_description": "Incorrect verses count in chapter", "error_list": result})
            
        # проверяем наличие лишних книг и глав
            
    except HTTPException as e:
        raise e
    finally:
        cursor.close()
        connection.close()
    return {"result_text": "Everything is OK"}

@router.get('/check_voice', operation_id="check_voice")
def check_translation(voice: Optional[int]):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        # проверка количества стихов
        sql = '''
			SELECT count(*) AS cc
			FROM voice_alignments
            WHERE voice = %(voice)s
		'''
        cursor.execute(sql, {
            'voice': voice
        })
        result = cursor.fetchall()
        verses_count = result[0]['cc']
        if verses_count != MUST_VERSES_COUNT:
            raise HTTPException(status_code=422, detail={"error_description": "Voices count (%s) is not correct (need %s)" % (verses_count, MUST_VERSES_COUNT)})
        
        # проверка стихов, где end > begin
        sql = '''
            SELECT tb.book_number, tb.name, tv.chapter_number, tv.verse_number, va.begin, va.end
            FROM voice_alignments AS va
              LEFT JOIN translation_verses AS tv ON tv.code = va.translation_verse
              LEFT JOIN translation_books AS tb ON tb.code = tv.translation_book
            WHERE va.voice = %(voice)s
              AND va.end <= va.begin
            LIMIT 100
        '''
        cursor.execute(sql, {
            'voice': voice
        })
        result = cursor.fetchall()
        if result:
            raise HTTPException(status_code=422, detail={"error_description": "begin >= end", "error_list": result})
    
    except HTTPException as e:
        raise e
    finally:
        cursor.close()
        connection.close()
    return {"result_text": "Everything is OK"}