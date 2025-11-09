-- Migration: reorder_translation_verses_columns
-- Created: 2025-11-09 14:53:00

-- Add your SQL statements here
-- Each statement should end with a semicolon

-- Reorder columns in translation_verses table
-- New order: code, book_number, chapter_number, verse_number, verse_number_join, start_paragraph, translation_book, text, html

ALTER TABLE `translation_verses` 
MODIFY COLUMN `book_number` smallint NOT NULL AFTER `code`,
MODIFY COLUMN `chapter_number` smallint NOT NULL AFTER `book_number`,
MODIFY COLUMN `verse_number` smallint NOT NULL AFTER `chapter_number`,
MODIFY COLUMN `verse_number_join` smallint NOT NULL DEFAULT 0 AFTER `verse_number`,
MODIFY COLUMN `start_paragraph` tinyint(1) NOT NULL AFTER `verse_number_join`,
MODIFY COLUMN `translation_book` int NOT NULL AFTER `start_paragraph`,
MODIFY COLUMN `text` varchar(10000) NOT NULL AFTER `translation_book`,
MODIFY COLUMN `html` varchar(10000) NOT NULL AFTER `text`;
