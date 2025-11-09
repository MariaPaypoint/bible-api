-- Migration: add_book_number_to_translation_verses
-- Created: 2025-11-09 13:36:00

-- Add your SQL statements here
-- Each statement should end with a semicolon

-- Add book_number field to translation_verses table
ALTER TABLE `translation_verses` 
ADD COLUMN `book_number` smallint NOT NULL DEFAULT 0 AFTER `translation_book`;

-- Add index for better performance
ALTER TABLE `translation_verses` 
ADD INDEX `idx_translation_verses_book_number` (`book_number`);

-- Add composite index for common queries
ALTER TABLE `translation_verses` 
ADD INDEX `idx_translation_verses_book_chapter_verse` (`book_number`, `chapter_number`, `verse_number`);
