"""
Тесты для обработки ошибок в аудио модуле
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from fastapi import HTTPException

from audio import create_range_response, get_voice_link_template, format_audio_url


class TestAudioErrorHandling:
    """Тесты обработки ошибок в аудио модуле"""

    def test_create_range_response_file_not_found_without_url(self):
        """Тест ошибки 404 без корректного URL"""
        non_existent_path = Path("/non/existent/file.mp3")
        
        with pytest.raises(HTTPException) as exc_info:
            create_range_response(non_existent_path, None)
        
        assert exc_info.value.status_code == 404
        error_detail = exc_info.value.detail
        assert isinstance(error_detail, dict)
        assert "Audio file not found on server" in error_detail['detail']
        assert str(non_existent_path.absolute()) in error_detail['detail']
        assert error_detail['alternative_url'] is None

    @patch('audio.get_voice_link_template')
    @patch('audio.format_audio_url')
    def test_create_range_response_file_not_found_with_url(self, mock_format_url, mock_get_template):
        """Тест ошибки 404 с корректным URL"""
        non_existent_path = Path("/non/existent/file.mp3")
        mock_get_template.return_value = "https://example.com/{book_zerofill}/{chapter_zerofill}.mp3"
        mock_format_url.return_value = "https://example.com/01/01.mp3"
        
        with pytest.raises(HTTPException) as exc_info:
            create_range_response(
                non_existent_path, None, 
                translation="syn", voice="bondarenko", 
                book="1", chapter="1"
            )
        
        assert exc_info.value.status_code == 404
        error_detail = exc_info.value.detail
        assert isinstance(error_detail, dict)
        assert "Audio file not found on server" in error_detail['detail']
        assert error_detail['alternative_url'] == "https://example.com/01/01.mp3"
        
        mock_get_template.assert_called_once_with("syn", "bondarenko")
        mock_format_url.assert_called_once_with(
            "https://example.com/{book_zerofill}/{chapter_zerofill}.mp3", "1", "1"
        )

    @patch('audio.create_connection')
    def test_get_voice_link_template_success(self, mock_create_connection):
        """Тест успешного получения link_template"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_create_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'link_template': 'https://example.com/{book_zerofill}/{chapter_zerofill}.mp3'
        }
        
        result = get_voice_link_template("syn", "bondarenko")
        
        assert result == 'https://example.com/{book_zerofill}/{chapter_zerofill}.mp3'
        mock_cursor.execute.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_connection.close.assert_called_once()

    @patch('audio.create_connection')
    def test_get_voice_link_template_not_found(self, mock_create_connection):
        """Тест случая, когда голос не найден"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_create_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        result = get_voice_link_template("unknown", "unknown")
        
        assert result == ''

    @patch('audio.create_connection')
    def test_get_voice_link_template_database_error(self, mock_create_connection):
        """Тест обработки ошибки базы данных"""
        mock_create_connection.side_effect = Exception("Database error")
        
        result = get_voice_link_template("syn", "bondarenko")
        
        assert result == ''

    @patch('audio.create_connection')
    def test_format_audio_url_success(self, mock_create_connection):
        """Тест успешного форматирования URL"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_create_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'number': 1,
            'code1': 'gen',
            'code2': 'gn',
            'code3': 'gen'
        }
        
        template = "https://example.com/{book_zerofill}/{chapter_zerofill}.mp3"
        result = format_audio_url(template, "1", "1")
        
        assert result == "https://example.com/01/01.mp3"

    def test_format_audio_url_empty_template(self):
        """Тест с пустым шаблоном"""
        result = format_audio_url("", "1", "1")
        assert result == ''

    @patch('audio.create_connection')
    def test_format_audio_url_book_not_found(self, mock_create_connection):
        """Тест случая, когда книга не найдена"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_create_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        template = "https://example.com/{book_zerofill}/{chapter_zerofill}.mp3"
        result = format_audio_url(template, "999", "1")
        
        assert result == ''
