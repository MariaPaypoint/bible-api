# models.py
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, Literal
from enum import Enum

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
    anomalies_count: int = 0

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

class AnomalyStatus(str, Enum):
    DETECTED = "detected"      # ошибка выявлена (по умолчанию)
    CONFIRMED = "confirmed"    # ошибка подтверждена
    DISPROVED = "disproved"    # ошибка опровергнута, не подтверждена проверкой
    CORRECTED = "corrected"    # выполнена ручная коррекция
    ALREADY_RESOLVED = "already_resolved" # уже исправлена ранее

class VoiceAnomalyModel(BaseModel):
    code: int
    voice: int
    translation: int
    book_number: int
    chapter_number: int
    verse_number: int  # Changed from Optional[int] to int (NOT NULL)
    word: Optional[str] = None  # Changed from str to Optional[str] (nullable)
    position_in_verse: Optional[int] = None
    position_from_end: Optional[int] = None
    duration: Optional[float] = None  # Changed from float to Optional[float] (nullable)
    speed: Optional[float] = None  # Changed from float to Optional[float] (nullable)
    ratio: float
    anomaly_type: str = 'fast'  # Changed from Optional[str] to str (NOT NULL)
    status: AnomalyStatus = AnomalyStatus.DETECTED
    verse_start_time: Optional[float] = None
    verse_end_time: Optional[float] = None
    verse_text: Optional[str] = None

class VoiceAnomaliesResponseModel(BaseModel):
    items: list[VoiceAnomalyModel]
    total_count: int

class AnomalyStatusUpdateModel(BaseModel):
    status: AnomalyStatus
    begin: Optional[float] = None  # New begin time for corrected status
    end: Optional[float] = None    # New end time for corrected status
    
    @model_validator(mode='after')
    def validate_correction_fields(self):
        """Validate begin/end fields based on status"""
        if self.status == AnomalyStatus.CORRECTED:
            if self.begin is None or self.end is None:
                raise ValueError('begin and end are required for corrected status')
            if self.begin >= self.end:
                raise ValueError('begin must be less than end')
        else:
            if self.begin is not None or self.end is not None:
                raise ValueError('begin and end are only allowed for corrected status')
        return self

# Translation Books

class TranslationBookModel(BaseModel):
    code: int
    book_number: int
    name: str
    alias: Optional[str] = None
    chapters_count: int
    anomalies_count: Optional[int] = None


# Audio Error Models

class AudioFileNotFoundError(BaseModel):
    detail: str
    alternative_url: Optional[str] = None

