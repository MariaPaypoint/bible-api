# models.py
from pydantic import BaseModel

class LanguageModel(BaseModel):
    alias: str
    name_en: str
    name_national: str

class VoiceModel(BaseModel):
    code: int
    alias: str
    name: str
    description: str
    is_music: bool

class TranslationModel(BaseModel):
    code: int
    alias: str
    name: str
    description: str
    language: str
    voices: list[VoiceModel]
