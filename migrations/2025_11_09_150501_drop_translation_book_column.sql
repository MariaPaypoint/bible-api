-- Migration: drop_translation_book_column
-- Created: 2025-11-09 15:05:01

-- Add your SQL statements here
-- Each statement should end with a semicolon

-- Drop the translation_book column as it's no longer needed
-- We now use translation and book_number columns instead

-- First, drop the foreign key constraint
ALTER TABLE `translation_verses` 
DROP FOREIGN KEY `translation_verses_translation_book`;

-- Then drop the index
ALTER TABLE `translation_verses` 
DROP INDEX `translation_book_idx`;

-- Finally, drop the column
ALTER TABLE `translation_verses` 
DROP COLUMN `translation_book`;
