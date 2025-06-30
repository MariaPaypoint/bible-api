from typing import Union, Optional

from fastapi import FastAPI, HTTPException
from database import create_connection
from models import *

from fastapi.routing import APIRoute

from excerpt import router as excerpt_router
from excerpt import get_books_info
from checks import router as checks_router
from audio import router as audio_router

app = FastAPI()

app.include_router(excerpt_router)
app.include_router(checks_router)
app.include_router(audio_router)


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
              LEFT JOIN voices  AS a ON a.translation = t.code AND a.active=1
            WHERE t.active=1
        '''
        if language:
            sql += " AND t.language = %s "
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

@app.get('/translation_info', response_model=TranslationInfoModel, operation_id="get_translation_info")
def get_translation_info(translation: int):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    result = []
    try:
        sql = '''
            SELECT code, alias, name, description, language
            FROM translations
            WHERE code = %(translation)s
              AND active=1
        '''
        cursor.execute(sql, { 'translation': translation })

        result = cursor.fetchone()
        if not result:
            raise HTTPException(
                status_code=422, 
                detail=f"Translation {translation} not found."
            )
		
        result['books_info'] = get_books_info(cursor, translation)
        
    except Exception as e:
        #raise HTTPException(status_code=500, detail=str(e))
        raise e
    finally:
        cursor.close()
        connection.close()
    return result



