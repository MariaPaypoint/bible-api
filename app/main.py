from typing import Union, Optional

from fastapi import FastAPI, HTTPException
from database import create_connection
from models import *

from fastapi.routing import APIRoute

from excerpt import router as excerpt_router

app = FastAPI()

app.include_router(excerpt_router)

@app.get('/languages', response_model=list[LanguageModel], operation_id="get_languages")
def get_languages():
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute('''
			SELECT alias, name_en, name_national 
			FROM languages
		''')
        result = cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()
    return result


@app.get('/translations', response_model=list[TranslationModel], operation_id="get_translations")
def get_translations(language: Optional[str] = None):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        params = []
        sql = '''
            SELECT 
				t.code        AS translation_code,
				t.alias       AS translation_alias,
				t.name        AS translation_name,
				t.description AS translation_description,
				t.language    AS translation_language,
				
				a.code        AS audio_code,
				a.alias       AS audio_alias,
				a.name        AS audio_name,
				a.description AS audio_description,
				a.is_music    AS audio_is_music
            FROM translations AS t
            LEFT JOIN voices  AS a ON a.translation = t.code
        '''
        if language:
            sql += " WHERE t.language = %s "
            params.append(language)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
		
        translations = {}
        for row in rows:
            translation_code = row['translation_code']
            if translation_code not in translations:
                translations[translation_code] = {
                    'code'        : translation_code,
                    'alias'       : row['translation_alias'],
                    'name'        : row['translation_name'],
                    'description' : row['translation_description'],
                    'language'    : row['translation_language'],
                    'voices'      : [],
                }
            if row['audio_code']:
                translations[translation_code]['voices'].append({
                    'code'        : row['audio_code'],
                    'alias'       : row['audio_alias'],
                    'name'        : row['audio_name'],
                    'description' : row['audio_description'],
                    'is_music'    : row['audio_is_music'],
                })
        
        result = list(translations.values())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()
    return result

@app.get('/check_translation', operation_id="check_translation")
def check_translation(translation: Optional[int]):
    MUST_VERSES_COUNT = 31240
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