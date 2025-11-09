-- Migration: populate_translation_in_translation_verses
-- Created: 2025-11-09 14:57:01

-- Add your SQL statements here
-- Each statement should end with a semicolon

-- Update translation_verses with translation from translation_books
UPDATE `translation_verses` tv
INNER JOIN `translation_books` tb ON tv.translation_book = tb.code
SET tv.translation = tb.translation
WHERE tv.translation = 0;
