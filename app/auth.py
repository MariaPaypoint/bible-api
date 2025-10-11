"""
Модуль авторизации для Bible API

Поддерживает два уровня защиты:
1. Статичный API ключ (X-API-Key) - для клиентских приложений
2. JWT токены (Authorization: Bearer) - для административных операций
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel

# Импортируем конфигурацию
try:
    from config import API_KEY, JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_HOURS, ADMIN_USERNAME, ADMIN_PASSWORD_HASH
except ImportError:
    # Значения по умолчанию для разработки (должны быть переопределены в config.py)
    API_KEY = "your-api-key-here"
    JWT_SECRET_KEY = "your-secret-key-here-change-in-production"
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_HOURS = 24
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD_HASH = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # "secret"

# Схемы безопасности
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


class Token(BaseModel):
    """Модель токена доступа"""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Данные из токена"""
    username: Optional[str] = None


class LoginRequest(BaseModel):
    """Запрос на авторизацию"""
    username: str
    password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Получение хеша пароля"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создание JWT токена
    
    Args:
        data: Данные для включения в токен
        expires_delta: Время жизни токена (по умолчанию из конфига)
    
    Returns:
        JWT токен
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> bool:
    """
    Проверка статичного API ключа из заголовка X-API-Key
    
    Используется для публичных эндпоинтов (GET запросы)
    """
    if api_key is None or api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key"
        )
    return True


def verify_api_key_query(api_key: Optional[str] = None) -> bool:
    """
    Проверка статичного API ключа из query параметра
    
    Используется для аудио эндпоинта (браузер не может отправлять кастомные заголовки)
    """
    if api_key is None or api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key"
        )
    return True


def verify_jwt_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)) -> str:
    """
    Проверка JWT токена
    
    Используется для административных эндпоинтов (POST/PUT/PATCH/DELETE)
    
    Returns:
        username из токена
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authenticate_user(username: str, password: str) -> bool:
    """
    Аутентификация пользователя по логину и паролю
    
    Args:
        username: Имя пользователя
        password: Пароль
    
    Returns:
        True если аутентификация успешна
    """
    if username != ADMIN_USERNAME:
        return False
    if not verify_password(password, ADMIN_PASSWORD_HASH):
        return False
    return True


# Зависимости для использования в эндпоинтах
RequireAPIKey = Depends(verify_api_key)
RequireJWT = Depends(verify_jwt_token)
