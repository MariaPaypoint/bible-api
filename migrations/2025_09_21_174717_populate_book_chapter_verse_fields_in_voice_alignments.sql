-- Migration: populate_book_chapter_verse_fields_in_voice_alignments
-- Created: 2025-09-21 17:47:17

-- Add your SQL statements here
-- Each statement should end with a semicolon

-- Update voice_alignments with book_number, chapter_number, verse_number from related tables
UPDATE `voice_alignments` va
INNER JOIN `translation_verses` tv ON va.translation_verse = tv.code
INNER JOIN `translation_books` tb ON tv.translation_book = tb.code
SET 
    va.book_number = tb.book_number,
    va.chapter_number = tv.chapter_number,
    va.verse_number = tv.verse_number
WHERE va.book_number = 0 OR va.chapter_number = 0 OR va.verse_number = 0;
