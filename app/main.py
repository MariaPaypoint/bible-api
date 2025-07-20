from typing import Union, Optional

from fastapi import FastAPI, HTTPException
from database import create_connection
from models import *

from fastapi.routing import APIRoute

from excerpt import router as excerpt_router
from excerpt import get_books_info
from checks import router as checks_router
from audio import router as audio_router

# Tags metadata for controlling order in Swagger UI
tags_metadata = [
    {
        "name": "Languages",
        "description": "",
    },
    {
        "name": "Translations",
        "description": "",
    },
    {
        "name": "Voices",
        "description": "",
    },
    {
        "name": "Excerpts",
        "description": "",
    },
    {
        "name": "Audio",
        "description": "Streaming & Download mp3",
    },
]

app = FastAPI(openapi_tags=tags_metadata)

app.include_router(excerpt_router)
app.include_router(checks_router)
app.include_router(audio_router)


@app.get('/languages', response_model=list[LanguageModel], operation_id="get_languages", tags=["Languages"])
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


@app.get('/translations', response_model=list[TranslationModel], operation_id="get_translations", tags=["Translations"])
def get_translations(language: Optional[str] = None, only_active: int = 1):
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
				t.active      AS translation_active,
				
				a.code        AS audio_code,
				a.alias       AS audio_alias,
				a.name        AS audio_name,
				a.description AS audio_description,
				a.is_music    AS audio_is_music,
				a.active      AS audio_active
            FROM translations AS t
              LEFT JOIN voices  AS a ON a.translation = t.code'''
        
        # Add active filter conditions based on only_active parameter
        if only_active == 1:
            sql += " WHERE t.active=1 AND (a.active=1 OR a.active IS NULL)"
        else:
            sql += " WHERE 1=1"
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
                    'active'      : row['translation_active'],
                    'voices'      : [],
                }
            if row['audio_code']:
                translations[translation_code]['voices'].append({
                    'code'        : row['audio_code'],
                    'alias'       : row['audio_alias'],
                    'name'        : row['audio_name'],
                    'description' : row['audio_description'],
                    'is_music'    : row['audio_is_music'],
                    'active'      : row['audio_active'],
                })
        
        result = list(translations.values())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()
    return result

@app.get('/translation_info', response_model=TranslationInfoModel, operation_id="get_translation_info", tags=["Translations"])
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


@app.get('/translations/{translation_code}/books', response_model=list[TranslationBookModel], operation_id="get_translation_books", tags=["Translations"])
def get_translation_books(translation_code: int):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        # Check if translation exists
        cursor.execute("SELECT code FROM translations WHERE code = %s AND active = 1", (translation_code,))
        translation = cursor.fetchone()
        if not translation:
            raise HTTPException(status_code=404, detail=f"Translation {translation_code} not found")
        
        # Get books for this translation with alias from bible_books
        cursor.execute('''
            SELECT 
                tb.code, tb.book_number, tb.name, bb.code1 AS alias,
                (SELECT COUNT(DISTINCT chapter_number) FROM translation_verses WHERE translation_book = tb.code) AS chapters_count
            FROM translation_books AS tb
            LEFT JOIN bible_books AS bb ON bb.number = tb.book_number
            WHERE tb.translation = %s
            ORDER BY tb.book_number
        ''', (translation_code,))
        
        books = cursor.fetchall()
        return books
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()


@app.put('/translations/{translation_code}', response_model=TranslationModel, operation_id="update_translation", tags=["Translations"])
def update_translation(translation_code: int, update_data: TranslationUpdateModel):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        # Check if translation exists
        cursor.execute("SELECT * FROM translations WHERE code = %s", (translation_code,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail=f"Translation {translation_code} not found")
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        if update_data.alias is not None:
            update_fields.append("alias = %s")
            params.append(update_data.alias)
        if update_data.name is not None:
            update_fields.append("name = %s")
            params.append(update_data.name)
        if update_data.description is not None:
            update_fields.append("description = %s")
            params.append(update_data.description)
        if update_data.language is not None:
            update_fields.append("language = %s")
            params.append(update_data.language)
        if update_data.active is not None:
            update_fields.append("active = %s")
            params.append(update_data.active)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Execute update
        params.append(translation_code)
        update_sql = f"UPDATE translations SET {', '.join(update_fields)} WHERE code = %s"
        cursor.execute(update_sql, params)
        connection.commit()
        
        # Return updated translation
        cursor.execute('''
            SELECT 
                t.code, t.alias, t.name, t.description, t.language, t.active,
                v.code as voice_code, v.alias as voice_alias, v.name as voice_name, 
                v.description as voice_description, v.is_music, v.active as voice_active
            FROM translations t
            LEFT JOIN voices v ON v.translation = t.code
            WHERE t.code = %s
        ''', (translation_code,))
        rows = cursor.fetchall()
        
        if not rows:
            raise HTTPException(status_code=404, detail=f"Translation {translation_code} not found")
        
        # Build response
        translation_data = {
            'code': rows[0]['code'],
            'alias': rows[0]['alias'],
            'name': rows[0]['name'],
            'description': rows[0]['description'],
            'language': rows[0]['language'],
            'active': rows[0]['active'],
            'voices': []
        }
        
        for row in rows:
            if row['voice_code']:
                translation_data['voices'].append({
                    'code': row['voice_code'],
                    'alias': row['voice_alias'],
                    'name': row['voice_name'],
                    'description': row['voice_description'],
                    'is_music': row['is_music'],
                    'active': row['voice_active']
                })
        
        return translation_data
        
    except Exception as e:
        connection.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()


@app.put('/voices/{voice_code}', response_model=VoiceModel, operation_id="update_voice", tags=["Voices"])
def update_voice(voice_code: int, update_data: VoiceUpdateModel):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        # Check if voice exists
        cursor.execute("SELECT * FROM voices WHERE code = %s", (voice_code,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail=f"Voice {voice_code} not found")
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        if update_data.alias is not None:
            update_fields.append("alias = %s")
            params.append(update_data.alias)
        if update_data.name is not None:
            update_fields.append("name = %s")
            params.append(update_data.name)
        if update_data.description is not None:
            update_fields.append("description = %s")
            params.append(update_data.description)
        if update_data.is_music is not None:
            update_fields.append("is_music = %s")
            params.append(update_data.is_music)
        if update_data.active is not None:
            update_fields.append("active = %s")
            params.append(update_data.active)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Execute update
        params.append(voice_code)
        update_sql = f"UPDATE voices SET {', '.join(update_fields)} WHERE code = %s"
        cursor.execute(update_sql, params)
        connection.commit()
        
        # Return updated voice
        cursor.execute('''
            SELECT code, alias, name, description, is_music, active
            FROM voices
            WHERE code = %s
        ''', (voice_code,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Voice {voice_code} not found")
        
        return result
        
    except Exception as e:
        connection.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()


@app.get('/voices/{voice_code}/anomalies', response_model=VoiceAnomaliesResponseModel, operation_id="get_voice_anomalies", tags=["Voices"])
def get_voice_anomalies(voice_code: int, page: int = 1, limit: int = 50, anomaly_type: Optional[str] = None, book_number: Optional[int] = None, sort_by: Optional[str] = None, sort_order: Optional[str] = None):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be >= 1")
        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
        
        # Validate sort_by parameter
        valid_sort_options = ["address", "type", "ratio"]
        if sort_by and sort_by not in valid_sort_options:
            raise HTTPException(status_code=400, detail=f"Invalid sort_by value. Must be one of: {', '.join(valid_sort_options)}")
        
        # Validate sort_order parameter
        valid_sort_orders = ["asc", "desc"]
        if sort_order and sort_order.lower() not in valid_sort_orders:
            raise HTTPException(status_code=400, detail=f"Invalid sort_order value. Must be one of: {', '.join(valid_sort_orders)}")
        
        # Check if voice exists
        cursor.execute("SELECT code FROM voices WHERE code = %s", (voice_code,))
        voice = cursor.fetchone()
        if not voice:
            raise HTTPException(status_code=404, detail=f"Voice {voice_code} not found")
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Build query parameters
        query_params = [voice_code]
        where_clause = "WHERE voice = %s"
        
        # Add anomaly_type filter if provided
        if anomaly_type:
            where_clause += " AND anomaly_type = %s"
            query_params.append(anomaly_type)
        
        # Add book_number filter if provided
        if book_number:
            where_clause += " AND book_number = %s"
            query_params.append(book_number)
        
        # Build ORDER BY clause based on sort_by and sort_order parameters
        sort_direction = "DESC" if sort_order and sort_order.lower() == "desc" else "ASC"
        
        if sort_by == "address":
            order_by = f"ORDER BY book_number {sort_direction}, chapter_number {sort_direction}, verse_number {sort_direction}, position_in_verse {sort_direction}"
        elif sort_by == "type":
            order_by = f"ORDER BY anomaly_type {sort_direction}, book_number ASC, chapter_number ASC, verse_number ASC, position_in_verse ASC"
        elif sort_by == "ratio":
            order_by = f"ORDER BY ratio {sort_direction}, book_number ASC, chapter_number ASC, verse_number ASC, position_in_verse ASC"
        else:
            # Default sorting by ratio DESC
            order_by = "ORDER BY ratio DESC, book_number, chapter_number, verse_number, position_in_verse"
        
        # Get total count first
        count_sql = f"SELECT COUNT(*) as total FROM voice_anomalies {where_clause}"
        cursor.execute(count_sql, query_params)
        total_count = cursor.fetchone()['total']
        
        # Get anomalies for this voice with pagination and filtering
        query_params.extend([limit, offset])
        cursor.execute(f'''
            SELECT code, voice, translation, book_number, chapter_number, 
                   verse_number, word, position_in_verse, position_from_end,
                   duration, speed, ratio, anomaly_type
            FROM voice_anomalies 
            {where_clause}
            {order_by}
            LIMIT %s OFFSET %s
        ''', query_params)
        
        anomalies = cursor.fetchall()
        return {
            "items": anomalies,
            "total_count": total_count
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()
