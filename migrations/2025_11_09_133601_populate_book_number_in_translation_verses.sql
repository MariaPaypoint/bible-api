-- Migration: populate_book_number_in_translation_verses
-- Created: 2025-11-09 13:36:01

-- Add your SQL statements here
-- Each statement should end with a semicolon

-- Update translation_verses with book_number from translation_books
UPDATE `translation_verses` tv
INNER JOIN `translation_books` tb ON tv.translation_book = tb.code
SET tv.book_number = tb.book_number
WHERE tv.book_number = 0;
