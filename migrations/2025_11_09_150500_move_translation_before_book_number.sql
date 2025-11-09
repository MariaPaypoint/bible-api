-- Migration: move_translation_before_book_number
-- Created: 2025-11-09 15:05:00

-- Add your SQL statements here
-- Each statement should end with a semicolon

-- Move translation column before book_number
ALTER TABLE `translation_verses` 
MODIFY COLUMN `translation` int NOT NULL AFTER `code`;
