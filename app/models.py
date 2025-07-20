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
    active: bool

class TranslationModel(BaseModel):
    code: int
    alias: str
    name: str
    description: Optional[str] = None
    language: str
    active: bool
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
    verse_code: Optional[int] = None
    title_code: Optional[int] = None
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

# Update Models

class TranslationUpdateModel(BaseModel):
    alias: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    active: Optional[bool] = None

class VoiceUpdateModel(BaseModel):
    alias: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_music: Optional[bool] = None
    active: Optional[bool] = None

# Voice Anomalies

class VoiceAnomalyModel(BaseModel):
    code: int
    voice: int
    translation: int
    book_number: int
    chapter_number: int
    verse_number: Optional[int] = None
    word: str
    position_in_verse: Optional[int] = None
    position_from_end: Optional[int] = None
    duration: float
    speed: float
    ratio: float
    anomaly_type: Optional[str] = 'fast'

class VoiceAnomaliesResponseModel(BaseModel):
    items: list[VoiceAnomalyModel]
    total_count: int

# Translation Books

class TranslationBookModel(BaseModel):
    code: int
    book_number: int
    name: str
    alias: Optional[str] = None
    chapters_count: int

