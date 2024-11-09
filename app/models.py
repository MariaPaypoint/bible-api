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
    begin: float
    end: float
    start_paragraph: bool

class PartsWithAlignmentModel(BaseModel):
    #book_code: int
    book_number: int
    #chapter_code: int
    chapter_number: int
    audio_link: str
    verses: list[VerseWithAlignmentModel]

class ExcerptWithAlignmentModel(BaseModel):
    title: str
    is_single_chapter: bool
    parts: list[PartsWithAlignmentModel]

# TranslationInfoModel

"""
class BookInfoModel(BaseModel):
    

class TranslationInfoModel(BaseModel):
    code: int
    alias: str
    name: str
    description: Optional[str] = None
    language: str
    books_info: list[BookInfoModel]

"""