# models.py
from pydantic import BaseModel
from typing import Optional

# Languages & Translations

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

# TranslationInfo

class BookInfoModel(BaseModel):
    code: int
    number: int
    alias: str
    name: str
    chapters_count: int

class TranslationInfoModel(BaseModel):
    code: int
    alias: str
    name: str
    description: Optional[str] = None
    language: str
    books_info: list[BookInfoModel]

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

class TitleModel(BaseModel):
    code: int
    text: str
    before_verse_code: int
    metadata: Optional[str] = None
    reference: Optional[str] = None

class PartsWithAlignmentModel(BaseModel):
    book: BookInfoModel
    chapter_number: int
    audio_link: str
    prev_excerpt: str
    next_excerpt: str
    verses: list[VerseWithAlignmentModel]
    notes: list[NoteModel]
    titles: list[TitleModel]

class ExcerptWithAlignmentModel(BaseModel):
    title: str
    is_single_chapter: bool
    parts: list[PartsWithAlignmentModel]


