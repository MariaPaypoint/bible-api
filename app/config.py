import os


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = _get_int("DB_PORT", 3306)
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "cep")

# Path to MP3 files storage
MP3_FILES_PATH = os.getenv("MP3_FILES_PATH", "audio")

# Base URL for audio files
AUDIO_BASE_URL = os.getenv("AUDIO_BASE_URL", "http://localhost:8000")

# API Authorization settings
API_KEY = os.getenv("API_KEY", "change-me-api-key")

# JWT settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-jwt-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_HOURS = _get_int("JWT_EXPIRE_HOURS", 24)

# Administrator credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")
