-- Migration: add_translation_to_translation_verses
-- Created: 2025-11-09 14:57:00

-- Add your SQL statements here
-- Each statement should end with a semicolon

-- Add translation field to translation_verses table
ALTER TABLE `translation_verses` 
ADD COLUMN `translation` int NOT NULL DEFAULT 0 AFTER `book_number`;

-- Add index for better performance
ALTER TABLE `translation_verses` 
ADD INDEX `idx_translation_verses_translation` (`translation`);

-- Add composite index for common queries
ALTER TABLE `translation_verses` 
ADD INDEX `idx_translation_verses_trans_book_chapter` (`translation`, `book_number`, `chapter_number`);
