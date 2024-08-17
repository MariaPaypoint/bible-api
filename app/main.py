from typing import Union, Optional

from fastapi import FastAPI, HTTPException
from database import create_connection
from models import *

from fastapi.routing import APIRoute

app = FastAPI()

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
            FROM bible_translations AS t
            LEFT JOIN audio_voices  AS a ON a.bible_translation = t.code
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


@app.get("/hello")
async def root():
    connection = create_connection()
    #cursor = connection.cursor(dictionary=True)
    return {"message": "Hello World"}

def use_route_names_as_operation_ids(app: FastAPI) -> None:
    """
    Simplify operation IDs so that generated API clients have simpler function
    names.

    Should be called only after all routes have been added.
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name  # in this case, 'read_items'