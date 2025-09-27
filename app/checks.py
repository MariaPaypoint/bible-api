from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional
from database import create_connection
from models import *

router = APIRouter()

MUST_VERSES_COUNT = 31240

@router.get('/check_translation', operation_id="check_translation", tags=["Translations"])
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

@router.get('/check_voice', operation_id="check_voice", tags=["Voices"])
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
        autdio_verses_count = result[0]['cc']

        sql = '''
			SELECT count(*) AS cc
			FROM translation_verses
            WHERE translation_book IN (
                SELECT code 
                FROM translation_books
                WHERE translation = (SELECT translation FROM voices WHERE code=%(voice)s)
            )
		'''
        cursor.execute(sql, {
            'voice': voice
        })
        result = cursor.fetchall()
        text_verses_count = result[0]['cc']

        if autdio_verses_count != text_verses_count:
            raise HTTPException(status_code=422, detail={"error_description": "Voices count (%s) is not correct (in text %s)" % (autdio_verses_count, text_verses_count)})
        
        # проверка стихов, где end > begin
        sql = '''
            SELECT 
              va.book_number, tb.name, va.chapter_number, va.verse_number, 
              CAST(va.begin AS float) AS begin, CAST(va.end AS float) as end, tv.text
            FROM voice_alignments AS va
              LEFT JOIN translation_verses AS tv ON (
                tv.verse_number = va.verse_number AND 
                tv.chapter_number = va.chapter_number AND
                tv.translation_book IN (
                  SELECT tb_inner.code 
                  FROM translation_books tb_inner 
                  WHERE tb_inner.book_number = va.book_number
                )
              )
              LEFT JOIN translation_books AS tb ON tb.book_number = va.book_number
            WHERE va.voice = %(voice)s
              AND va.end <= va.begin
              AND tv.text != '[]'
            LIMIT 100
        '''
        cursor.execute(sql, {
            'voice': voice
        })
        result = cursor.fetchall()
        if result:
            raise HTTPException(status_code=422, detail={"error_description": "begin >= end", "error_list": result})

        # проверка следующих стихов - должен быть begin больше предыдущего
        sql = '''
            SELECT 
              va.book_number, tb.name, va.chapter_number, va.verse_number, tv.text, 
              CAST(va.begin AS float) AS begin, CAST(va.end AS float) AS end, 
              CAST(next_va.begin AS float) AS next_begin
            FROM voice_alignments AS va
              LEFT JOIN translation_verses AS tv ON (
                tv.verse_number = va.verse_number AND 
                tv.chapter_number = va.chapter_number AND
                tv.translation_book IN (
                  SELECT tb_inner.code 
                  FROM translation_books tb_inner 
                  WHERE tb_inner.book_number = va.book_number
                )
              )
              LEFT JOIN translation_books AS tb ON tb.book_number = va.book_number
              LEFT JOIN voice_alignments AS next_va ON next_va.code = va.code+1
            WHERE va.voice = %(voice)s
              AND ( next_va.begin < va.end 
                AND next_va.book_number = va.book_number
                AND next_va.chapter_number = va.chapter_number 
              )
            LIMIT 100
        '''
        cursor.execute(sql, {
            'voice': voice
        })
        result = cursor.fetchall()
        if result:
            raise HTTPException(status_code=422, detail={"error_description": "next begin < current end", "error_list": result})

    except HTTPException as e:
        raise e
    finally:
        cursor.close()
        connection.close()
    return {"result_text": "Everything is OK"}
