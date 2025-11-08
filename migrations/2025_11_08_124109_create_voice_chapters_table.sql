-- Migration: create_voice_chapters_table
-- Created: 2025-11-08 12:41:09

-- Add your SQL statements here
-- Each statement should end with a semicolon

CREATE TABLE `voice_chapters` (
  `code` int NOT NULL AUTO_INCREMENT,
  `voice` int NOT NULL,
  `book_number` smallint NOT NULL,
  `chapter_number` smallint NOT NULL,
  `in_text` text NOT NULL,
  `out_json` json NOT NULL,
  `timecodes` json NOT NULL,
  PRIMARY KEY (`code`),
  UNIQUE KEY `idx_voice_chapters_unique` (`voice`, `book_number`, `chapter_number`),
  KEY `idx_voice_chapters_voice` (`voice`),
  KEY `idx_voice_chapters_book` (`book_number`),
  KEY `idx_voice_chapters_chapter` (`chapter_number`),
  CONSTRAINT `voice_chapters_voice` FOREIGN KEY (`voice`) REFERENCES `voices` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
