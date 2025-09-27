-- Migration: add_book_chapter_verse_fields_to_voice_alignments
-- Created: 2025-09-21 17:47:16

-- Add your SQL statements here
-- Each statement should end with a semicolon

-- Add new fields to voice_alignments table
ALTER TABLE `voice_alignments` 
ADD COLUMN `book_number` smallint NOT NULL DEFAULT 0 AFTER `translation_verse`,
ADD COLUMN `chapter_number` smallint NOT NULL DEFAULT 0 AFTER `book_number`,
ADD COLUMN `verse_number` smallint NOT NULL DEFAULT 0 AFTER `chapter_number`;

-- Change translation_verse type to INT NULL
ALTER TABLE `voice_alignments` 
CHANGE COLUMN `translation_verse` `translation_verse` INT NULL ;

-- Add indexes for better performance
ALTER TABLE `voice_alignments` 
ADD INDEX `idx_voice_alignments_book_chapter_verse` (`voice`, `book_number`, `chapter_number`, `verse_number`),
ADD INDEX `idx_voice_alignments_book_number` (`book_number`),
ADD INDEX `idx_voice_alignments_chapter_number` (`chapter_number`),
ADD INDEX `idx_voice_alignments_verse_number` (`verse_number`);

ALTER TABLE `bible_pause`.`translation_books` 
CHANGE COLUMN `translation` `translation` INT NOT NULL AFTER `code`;

ALTER TABLE `bible_pause`.`translation_books` 
ADD UNIQUE INDEX `unique_book` (`translation` ASC, `book_number` ASC) VISIBLE;