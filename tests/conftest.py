"""
Pytest конфигурация и фикстуры для тестов
"""
import pytest
import requests
from fastapi.testclient import TestClient
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

BASE_URL = "http://localhost:8000"
API_KEY = "bible-api-key-2024"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

@pytest.fixture(scope="session")
def api_key():
    """Возвращает API ключ для публичных эндпоинтов"""
    return API_KEY

@pytest.fixture(scope="session")
def api_headers(api_key):
    """Возвращает заголовки с API ключом"""
    return {"X-API-Key": api_key}

@pytest.fixture(scope="session")
def admin_token():
    """Получает JWT токен для административных операций"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )
    if response.status_code != 200:
        pytest.fail(f"Failed to get admin token: {response.status_code} - {response.text}")
    return response.json()["access_token"]

@pytest.fixture(scope="session")
def admin_headers(admin_token):
    """Возвращает заголовки с JWT токеном"""
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture(scope="session")
def base_url():
    """Возвращает базовый URL API"""
    return BASE_URL

@pytest.fixture(scope="function", autouse=True)
def inject_headers(request, api_headers, admin_headers):
    """
    Автоматически добавляет заголовки авторизации ко всем запросам TestClient
    """
    from fastapi.testclient import TestClient as OriginalTestClient
    from app.main import app
    
    # Сохраняем оригинальный метод request
    original_request = OriginalTestClient.request
    
    def patched_request(self, method, url, **kwargs):
        # Определяем, какие заголовки нужны based on HTTP method
        if 'headers' not in kwargs or kwargs['headers'] is None:
            kwargs['headers'] = {}
        
        if method.upper() in ['GET']:
            # GET запросы используют API ключ
            if 'X-API-Key' not in kwargs['headers']:
                kwargs['headers'].update(api_headers)
        else:
            # POST/PUT/PATCH/DELETE используют JWT токен
            if 'Authorization' not in kwargs['headers']:
                kwargs['headers'].update(admin_headers)
        
        return original_request(self, method, url, **kwargs)
    
    # Патчим метод request
    OriginalTestClient.request = patched_request
    
    yield
    
    # Восстанавливаем оригинальный метод
    OriginalTestClient.request = original_request
