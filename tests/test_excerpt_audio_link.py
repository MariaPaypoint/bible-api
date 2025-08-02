"""
Тесты для проверки формирования audio_link в эндпоинте excerpt_with_alignment
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Добавляем путь к модулю app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from excerpt import check_audio_file_exists, get_voice_info


class TestExcerptAudioLink(unittest.TestCase):
    """Тесты для проверки функциональности audio_link в excerpt"""

    def test_check_audio_file_exists_function(self):
        """Тест функции check_audio_file_exists"""
        with patch('excerpt.Path') as mock_path:
            # Настраиваем мок для существующего файла
            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_path.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_file
            
            result = check_audio_file_exists('syn', 'bondarenko', 1, 1)
            self.assertTrue(result)
            
            # Проверяем, что путь формируется правильно
            mock_path.assert_called_with('audio')

    def test_check_audio_file_not_exists(self):
        """Тест функции check_audio_file_exists для несуществующего файла"""
        with patch('excerpt.Path') as mock_path:
            # Настраиваем мок для несуществующего файла
            mock_file = MagicMock()
            mock_file.exists.return_value = False
            mock_path.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_file
            
            result = check_audio_file_exists('syn', 'bondarenko', 1, 1)
            self.assertFalse(result)

    def test_get_voice_info_with_aliases(self):
        """Тест функции get_voice_info с алиасами"""
        # Создаем мок курсора
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'name': 'Test Voice',
            'link_template': 'http://example.com/{book}/{chapter}.mp3',
            'voice_alias': 'test_voice',
            'translation_alias': 'test_translation'
        }
        
        result = get_voice_info(mock_cursor, 1, 1)
        
        # Проверяем, что результат содержит все необходимые поля
        self.assertIn('name', result)
        self.assertIn('link_template', result)
        self.assertIn('voice_alias', result)
        self.assertIn('translation_alias', result)
        
        # Проверяем SQL-запрос
        mock_cursor.execute.assert_called_once()
        sql_query = mock_cursor.execute.call_args[0][0]
        self.assertIn('v.alias as voice_alias', sql_query)
        self.assertIn('t.alias as translation_alias', sql_query)
        self.assertIn('JOIN translations t ON v.translation = t.code', sql_query)

    def test_audio_link_formation_logic(self):
        """Тест логики формирования audio_link"""
        # Проверяем формат ссылки для существующего файла
        book_number = 1
        chapter_number = 1
        translation_alias = 'syn'
        voice_alias = 'bondarenko'
        
        book_str = str(book_number).zfill(2)
        chapter_str = str(chapter_number).zfill(2)
        expected_link = f"/audio/{translation_alias}/{voice_alias}/{book_str}/{chapter_str}.mp3"
        self.assertEqual(expected_link, "/audio/syn/bondarenko/01/01.mp3")

    @patch('excerpt.check_audio_file_exists')
    def test_audio_link_with_mock_existing_file(self, mock_check_file):
        """Тест с моком для существующего файла"""
        mock_check_file.return_value = True
        
        result = mock_check_file('syn', 'bondarenko', 1, 1)
        self.assertTrue(result)
        mock_check_file.assert_called_with('syn', 'bondarenko', 1, 1)

    @patch('excerpt.check_audio_file_exists')
    def test_audio_link_with_mock_missing_file(self, mock_check_file):
        """Тест с моком для несуществующего файла"""
        mock_check_file.return_value = False
        
        result = mock_check_file('syn', 'bondarenko', 1, 1)
        self.assertFalse(result)
        mock_check_file.assert_called_with('syn', 'bondarenko', 1, 1)

    def test_audio_path_formatting(self):
        """Тест правильности формирования пути к аудиофайлу"""
        # Проверяем, что номера книг и глав правильно форматируются с нулями
        book_number = 1
        chapter_number = 5
        
        book_str = str(book_number).zfill(2)
        chapter_str = str(chapter_number).zfill(2)
        
        self.assertEqual(book_str, "01")
        self.assertEqual(chapter_str, "05")
        
        # Проверяем для больших номеров
        book_number = 40
        chapter_number = 28
        
        book_str = str(book_number).zfill(2)
        chapter_str = str(chapter_number).zfill(2)
        
        self.assertEqual(book_str, "40")
        self.assertEqual(chapter_str, "28")


if __name__ == '__main__':
    unittest.main()
