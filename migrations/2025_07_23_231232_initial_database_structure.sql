-- Migration: initial_database_structure
-- Created: 2025-07-23 23:12:32

-- Add your SQL statements here
-- Each statement should end with a semicolon

CREATE TABLE `bible_books` (
  `number` int NOT NULL,
  `code1` varchar(45) NOT NULL,
  `code2` varchar(45) NOT NULL,
  `code3` varchar(45) NOT NULL,
  `code4` varchar(45) NOT NULL,
  `code5` varchar(45) NOT NULL,
  `code6` varchar(45) NOT NULL,
  `code7` varchar(45) NOT NULL,
  `code8` varchar(45) NOT NULL,
  `code9` varchar(45) NOT NULL,
  `verse_count` int NOT NULL,
  `short_name_en` varchar(45) NOT NULL,
  `short_name_ru` varchar(45) NOT NULL,
  `short_name_uk` varchar(45) NOT NULL,
  `full_name_en` varchar(255) NOT NULL,
  `full_name_ru` varchar(255) NOT NULL,
  `full_name_uk` varchar(255) NOT NULL,
  PRIMARY KEY (`number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `bible_stat` (
  `inc` int NOT NULL AUTO_INCREMENT,
  `book_number` smallint NOT NULL,
  `chapter_number` smallint NOT NULL,
  `verses_count` smallint NOT NULL,
  `tolerance_count` smallint NOT NULL,
  PRIMARY KEY (`inc`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `languages` (
  `alias` varchar(10) NOT NULL,
  `name_en` varchar(255) NOT NULL,
  `name_national` varchar(255) NOT NULL,
  PRIMARY KEY (`alias`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `phinxlog` (
  `version` bigint NOT NULL,
  `migration_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `start_time` timestamp NULL DEFAULT NULL,
  `end_time` timestamp NULL DEFAULT NULL,
  `breakpoint` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `translation_books` (
  `code` int NOT NULL AUTO_INCREMENT,
  `book_number` smallint NOT NULL COMMENT 'from table dict_universal_books',
  `translation` int NOT NULL,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`code`),
  KEY `translation_idx` (`translation`),
  KEY `book_number_idx` (`book_number`),
  CONSTRAINT `translation_books_translation` FOREIGN KEY (`translation`) REFERENCES `translations` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `translation_notes` (
  `code` int NOT NULL AUTO_INCREMENT,
  `translation_verse` int DEFAULT NULL,
  `translation_title` int DEFAULT NULL,
  `position_text` smallint NOT NULL,
  `position_html` smallint NOT NULL,
  `note_number` int NOT NULL,
  `text` varchar(10000) NOT NULL,
  PRIMARY KEY (`code`),
  KEY `translation_verse_idx` (`translation_verse`),
  KEY `translation_title_idx` (`translation_title`),
  CONSTRAINT `translation_notes_translation_title` FOREIGN KEY (`translation_title`) REFERENCES `translation_titles` (`code`),
  CONSTRAINT `translation_notes_translation_verse` FOREIGN KEY (`translation_verse`) REFERENCES `translation_verses` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `translation_titles` (
  `code` int NOT NULL AUTO_INCREMENT,
  `before_translation_verse` int NOT NULL,
  `text` varchar(1000) NOT NULL,
  `metadata` varchar(1000) DEFAULT NULL,
  `reference` varchar(1000) DEFAULT NULL,
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `translation_verses` (
  `code` int NOT NULL AUTO_INCREMENT,
  `verse_number` smallint NOT NULL,
  `verse_number_join` smallint NOT NULL DEFAULT '0',
  `chapter_number` smallint NOT NULL,
  `translation_book` int NOT NULL,
  `text` varchar(10000) NOT NULL,
  `html` varchar(10000) NOT NULL,
  `start_paragraph` tinyint(1) NOT NULL,
  PRIMARY KEY (`code`),
  KEY `translation_book_idx` (`translation_book`),
  KEY `chapter_number_idx` (`chapter_number`),
  CONSTRAINT `translation_verses_translation_book` FOREIGN KEY (`translation_book`) REFERENCES `translation_books` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `translations` (
  `code` int NOT NULL AUTO_INCREMENT,
  `alias` varchar(50) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `bibleComDigitCode` varchar(50) DEFAULT NULL,
  `removeChapters` varchar(255) DEFAULT NULL,
  `language` varchar(10) NOT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`code`),
  KEY `language_idx` (`language`),
  CONSTRAINT `translations_language` FOREIGN KEY (`language`) REFERENCES `languages` (`alias`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `voice_alignments` (
  `code` int NOT NULL AUTO_INCREMENT,
  `voice` int NOT NULL,
  `translation_verse` int NOT NULL,
  `begin` decimal(10,3) NOT NULL,
  `end` decimal(10,3) NOT NULL,
  `is_correct` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`code`),
  KEY `voice_alignments_voice_idx` (`voice`),
  KEY `voice_alignments_translation_verse_idx` (`translation_verse`),
  CONSTRAINT `voice_alignments_voice` FOREIGN KEY (`voice`) REFERENCES `voices` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `voice_anomalies` (
  `code` int NOT NULL AUTO_INCREMENT,
  `voice` int NOT NULL,
  `translation` int NOT NULL,
  `book_number` smallint NOT NULL,
  `chapter_number` smallint NOT NULL,
  `verse_number` smallint DEFAULT NULL,
  `translation_verse_id` int DEFAULT NULL,
  `word` varchar(100) NOT NULL,
  `position_in_verse` smallint DEFAULT NULL,
  `position_from_end` smallint DEFAULT NULL,
  `duration` decimal(7,3) NOT NULL,
  `speed` decimal(7,2) NOT NULL,
  `ratio` decimal(7,2) NOT NULL,
  `anomaly_type` varchar(30) DEFAULT 'fast',
  PRIMARY KEY (`code`),
  KEY `idx_voice_anomalies_verse` (`voice`,`translation_verse_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `voice_manual_fixes` (
  `code` int NOT NULL AUTO_INCREMENT,
  `voice` int NOT NULL,
  `book_number` int NOT NULL,
  `chapter_number` int NOT NULL,
  `verse_number` int NOT NULL,
  `begin` decimal(10,3) NOT NULL,
  `end` decimal(10,3) NOT NULL,
  `info` varchar(10000) DEFAULT NULL,
  PRIMARY KEY (`code`),
  KEY `voice_alignments_manual_voice_idx` (`voice`),
  CONSTRAINT `voice_alignments_manual_voice_idx` FOREIGN KEY (`voice`) REFERENCES `voices` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `voices` (
  `code` int NOT NULL AUTO_INCREMENT,
  `alias` varchar(50) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` varchar(1000) DEFAULT NULL,
  `translation` int NOT NULL,
  `is_music` tinyint(1) NOT NULL,
  `link_template` varchar(1000) DEFAULT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`code`),
  KEY `translation_idx` (`translation`),
  CONSTRAINT `voices_translation` FOREIGN KEY (`translation`) REFERENCES `translations` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
