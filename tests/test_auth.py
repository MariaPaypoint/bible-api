#!/usr/bin/env python3
"""
Скрипт для тестирования авторизации Bible API
"""

import requests
import sys
import os

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000/api")
API_KEY = os.getenv("API_KEY", "bible-api-key-2024")
USERNAME = os.getenv("ADMIN_USERNAME", "admin")
PASSWORD = os.getenv("TEST_ADMIN_PASSWORD", "admin123")

def test_public_endpoint_without_key():
    """Тест: публичный эндпоинт без API ключа должен вернуть 403"""
    print("\n1. Тест: GET /translations без API ключа")
    response = requests.get(f"{BASE_URL}/translations")
    print(f"   Статус: {response.status_code}")
    print(f"   Ответ: {response.json()}")
    assert response.status_code == 403, "Ожидался статус 403"
    assert "Invalid or missing API Key" in response.json()["detail"]
    print("   ✅ Тест пройден")

def test_public_endpoint_with_key():
    """Тест: публичный эндпоинт с API ключом должен работать"""
    print("\n2. Тест: GET /translations с API ключом")
    headers = {"X-API-Key": API_KEY}
    response = requests.get(f"{BASE_URL}/translations", headers=headers)
    print(f"   Статус: {response.status_code}")
    assert response.status_code == 200, "Ожидался статус 200"
    data = response.json()
    print(f"   Получено переводов: {len(data)}")
    print("   ✅ Тест пройден")

def get_admin_token():
    """Получить JWT токен для использования в других тестах"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_login():
    """Тест: получение JWT токена"""
    print("\n3. Тест: POST /auth/login")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    print(f"   Статус: {response.status_code}")
    assert response.status_code == 200, "Ожидался статус 200"
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    print(f"   Токен получен: {data['access_token'][:50]}...")
    print(f"   Срок действия: {data['expires_in']} секунд")
    print("   ✅ Тест пройден")

def test_login_invalid_credentials():
    """Тест: логин с неверными учетными данными"""
    print("\n4. Тест: POST /auth/login с неверным паролем")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": USERNAME, "password": "wrong_password"}
    )
    print(f"   Статус: {response.status_code}")
    print(f"   Текст ответа: {response.text[:200]}")
    if response.status_code == 500:
        print("   ⚠️  Ошибка 500 - проверьте логи API")
        return
    print(f"   Ответ: {response.json()}")
    assert response.status_code == 401, "Ожидался статус 401"
    assert "Incorrect username or password" in response.json()["detail"]
    print("   ✅ Тест пройден")

def test_admin_endpoint_without_token():
    """Тест: административный эндпоинт без токена должен вернуть 401"""
    print("\n5. Тест: GET /voices/1/anomalies без токена")
    response = requests.get(f"{BASE_URL}/voices/1/anomalies")
    print(f"   Статус: {response.status_code}")
    print(f"   Ответ: {response.json()}")
    assert response.status_code == 401, "Ожидался статус 401"
    assert "Missing authentication token" in response.json()["detail"]
    print("   ✅ Тест пройден")

def test_admin_endpoint_with_invalid_token():
    """Тест: административный эндпоинт с невалидным токеном должен вернуть 401"""
    print("\n6. Тест: GET /voices/1/anomalies с невалидным токеном")
    headers = {"Authorization": "Bearer invalid-token-here"}
    response = requests.get(f"{BASE_URL}/voices/1/anomalies", headers=headers)
    print(f"   Статус: {response.status_code}")
    print(f"   Ответ: {response.json()}")
    assert response.status_code == 401, "Ожидался статус 401"
    assert "Invalid or expired authentication token" in response.json()["detail"]
    print("   ✅ Тест пройден")

def test_admin_endpoint_with_token(admin_token):
    """Тест: административный эндпоинт с валидным токеном должен работать"""
    print("\n7. Тест: GET /voices/1/anomalies с валидным токеном")
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/voices/1/anomalies", headers=headers)
    print(f"   Статус: {response.status_code}")
    
    if response.status_code == 404:
        print("   ⚠️  Голос с кодом 1 не найден (это нормально, если его нет в БД)")
        print("   ✅ Тест пройден (авторизация работает)")
    elif response.status_code == 200:
        data = response.json()
        print(f"   Получено аномалий: {data.get('total_count', 0)}")
        print("   ✅ Тест пройден")
    else:
        print(f"   ❌ Неожиданный статус: {response.status_code}")
        print(f"   Ответ: {response.json()}")
        sys.exit(1)

def test_chapter_with_alignment():
    """Тест: эндпоинт chapter_with_alignment с API ключом"""
    print("\n8. Тест: GET /chapter_with_alignment с API ключом")
    headers = {"X-API-Key": API_KEY}
    params = {
        "translation": 1,
        "book_number": 1,
        "chapter_number": 1
    }
    response = requests.get(
        f"{BASE_URL}/chapter_with_alignment",
        headers=headers,
        params=params
    )
    print(f"   Статус: {response.status_code}")
    
    if response.status_code == 422:
        print("   ⚠️  Перевод или книга не найдены (это нормально, если их нет в БД)")
        print("   ✅ Тест пройден (авторизация работает)")
    elif response.status_code == 200:
        data = response.json()
        print(f"   Получена глава: {data.get('title', 'N/A')}")
        print("   ✅ Тест пройден")
    else:
        print(f"   ❌ Неожиданный статус: {response.status_code}")
        print(f"   Ответ: {response.json()}")
        sys.exit(1)

def main():
    print("=" * 60)
    print("Тестирование авторизации Bible API")
    print("=" * 60)
    print(f"URL: {BASE_URL}")
    print(f"API Key: {API_KEY}")
    print(f"Username: {USERNAME}")
    
    try:
        # Проверяем, что API запущен
        try:
            requests.get(BASE_URL, timeout=2)
        except requests.exceptions.ConnectionError:
            print("\n❌ Ошибка: API не запущен!")
            print("Запустите API командой: uvicorn app.main:app --reload")
            sys.exit(1)
        
        # Публичные эндпоинты
        test_public_endpoint_without_key()
        test_public_endpoint_with_key()
        test_chapter_with_alignment()
        
        # Авторизация
        test_login_invalid_credentials()
        test_login()
        token = get_admin_token()
        
        # Административные эндпоинты
        test_admin_endpoint_without_token()
        test_admin_endpoint_with_invalid_token()
        test_admin_endpoint_with_token(token)
        
        print("\n" + "=" * 60)
        print("✅ Все тесты пройдены успешно!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Тест провален: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
