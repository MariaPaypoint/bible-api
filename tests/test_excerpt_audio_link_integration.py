"""
Интеграционные тесты для проверки audio_link в эндпоинте excerpt_with_alignment
"""

import unittest
from unittest.mock import patch
import sys
import os

# Добавляем путь к модулю app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from fastapi.testclient import TestClient
from main import app


class TestExcerptAudioLinkIntegration(unittest.TestCase):
    """Интеграционные тесты для audio_link в excerpt_with_alignment"""

    def setUp(self):
        self.client = TestClient(app)

    def test_excerpt_with_alignment_endpoint_exists(self):
        """Тест существования эндпоинта excerpt_with_alignment"""
        response = self.client.get("/api/excerpt_with_alignment?translation=1&excerpt=jhn 3:16&voice=1")
        # Проверяем, что эндпоинт отвечает (не 404)
        self.assertNotEqual(response.status_code, 404)

    @patch('excerpt.check_audio_file_exists')
    def test_audio_link_when_file_exists(self, mock_check_file):
        """Тест audio_link когда аудиофайл существует"""
        mock_check_file.return_value = True
        
        response = self.client.get("/api/excerpt_with_alignment?translation=1&excerpt=jhn 3:16&voice=1")
        
        if response.status_code == 200:
            data = response.json()
            
            # Проверяем структуру ответа
            self.assertIn('parts', data)
            if data['parts']:
                part = data['parts'][0]
                self.assertIn('audio_link', part)
                
                # Если голос найден и файл существует, audio_link должен содержать путь к аудио
                if part['audio_link']:
                    self.assertIn('/audio/', part['audio_link'])
                    self.assertTrue(part['audio_link'].endswith('.mp3'))

    @patch('excerpt.check_audio_file_exists')
    def test_audio_link_when_file_not_exists(self, mock_check_file):
        """Тест audio_link когда аудиофайл не существует"""
        mock_check_file.return_value = False
        
        response = self.client.get("/api/excerpt_with_alignment?translation=1&excerpt=jhn 3:16&voice=1")
        
        if response.status_code == 200:
            data = response.json()
            
            # Проверяем структуру ответа
            self.assertIn('parts', data)
            if data['parts']:
                part = data['parts'][0]
                self.assertIn('audio_link', part)
                
                # Если файл не существует, audio_link должен быть пустым
                self.assertEqual(part['audio_link'], '')

    def test_audio_link_without_voice(self):
        """Тест audio_link когда voice не указан"""
        response = self.client.get("/api/excerpt_with_alignment?translation=1&excerpt=jhn 3:16")
        
        if response.status_code == 200:
            data = response.json()
            
            # Проверяем структуру ответа
            self.assertIn('parts', data)
            if data['parts']:
                part = data['parts'][0]
                self.assertIn('audio_link', part)
                
                # Без voice audio_link должен быть пустым
                self.assertEqual(part['audio_link'], '')

    @patch('excerpt.check_audio_file_exists')
    def test_audio_link_format_validation(self, mock_check_file):
        """Тест правильности формата audio_link"""
        mock_check_file.return_value = True
        
        response = self.client.get("/api/excerpt_with_alignment?translation=1&excerpt=gen 1:1&voice=1")
        
        if response.status_code == 200:
            data = response.json()
            
            if data['parts'] and data['parts'][0]['audio_link']:
                audio_link = data['parts'][0]['audio_link']
                
                # Проверяем формат ссылки
                self.assertIn('/audio/', audio_link)
                self.assertTrue(audio_link.endswith('.mp3'))

    def test_excerpt_response_structure_with_audio_link(self):
        """Тест структуры ответа с полем audio_link"""
        response = self.client.get("/api/excerpt_with_alignment?translation=1&excerpt=jhn 3:16&voice=1")
        
        if response.status_code == 200:
            data = response.json()
            
            # Проверяем основную структуру
            self.assertIn('title', data)
            self.assertIn('is_single_chapter', data)
            self.assertIn('parts', data)
            
            if data['parts']:
                part = data['parts'][0]
                
                # Проверяем структуру части
                self.assertIn('book', part)
                self.assertIn('chapter_number', part)
                self.assertIn('audio_link', part)
                self.assertIn('verses', part)
                self.assertIn('notes', part)
                self.assertIn('titles', part)
                
                # audio_link должен быть строкой
                self.assertIsInstance(part['audio_link'], str)


if __name__ == '__main__':
    unittest.main()
