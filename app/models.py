# models.py
from pydantic import BaseModel
from typing import Optional

class LanguageModel(BaseModel):
    alias: str
    name_en: str
    name_national: str

class VoiceModel(BaseModel):
    code: int
    alias: str
    name: str
    description: Optional[str] = None
    is_music: bool

class TranslationModel(BaseModel):
    code: int
    alias: str
    name: str
    description: Optional[str] = None
    language: str
    voices: list[VoiceModel]

# ExcerptWithAlignment
    
class VerseWithAlignmentModel(BaseModel):
    code: int
    number: int
    join: int
    text: str
    html: str
    begin: float
    end: float
    start_paragraph: bool

class NoteModel(BaseModel):
    code: int
    number: int
    text: str
    verse_code: int
    position_text: int
    position_html: int

class PartsWithAlignmentModel(BaseModel):
    #book_code: int
    book_number: int
    #chapter_code: int
    chapter_number: int
    audio_link: str
    verses: list[VerseWithAlignmentModel]
    notes: list[NoteModel]

class ExcerptWithAlignmentModel(BaseModel):
    title: str
    is_single_chapter: bool
    parts: list[PartsWithAlignmentModel]



"""
# TranslationInfo

class BookInfoModel(BaseModel):
    

class TranslationInfoModel(BaseModel):
    code: int
    alias: str
    name: str
    description: Optional[str] = None
    language: str
    books_info: list[BookInfoModel]

"""