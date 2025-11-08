DB_HOST     = "your_mysql_host"
DB_PORT     = 3306
DB_USER     = "your_mysql_user"
DB_PASSWORD = "your_mysql_password"
DB_NAME     = "your_database_name"

# Path to MP3 files storage
MP3_FILES_PATH = "audio"

# Base URL for audio files
AUDIO_BASE_URL = "http://your-server:8000"

# API Authorization settings
# Static API key for client applications (GET requests)
API_KEY = "your-api-key-here"

# JWT settings for administrative operations
# Generate secret key: openssl rand -hex 32
JWT_SECRET_KEY = "your-secret-key-change-this-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24  # Token is valid for 24 hours

# Administrator credentials
ADMIN_USERNAME = "admin"
# Password hash
# To generate: python -c "import bcrypt; print(bcrypt.hashpw(b'your_password', bcrypt.gensalt()).decode('utf-8'))"
ADMIN_PASSWORD_HASH = "your-bcrypt-password-hash"