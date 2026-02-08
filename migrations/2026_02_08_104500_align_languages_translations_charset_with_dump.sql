-- Migration: align_languages_translations_charset_with_dump
-- Created: 2026-02-08 10:45:00

-- Align FK-compatible definitions with production dump format (utf8mb3)
SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `translations` DROP FOREIGN KEY `translations_language`;

ALTER TABLE `languages`
  CONVERT TO CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci,
  MODIFY COLUMN `alias` VARCHAR(10)
    CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL;

ALTER TABLE `translations`
  CONVERT TO CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci,
  MODIFY COLUMN `language` VARCHAR(10)
    CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL;

ALTER TABLE `translations`
  ADD CONSTRAINT `translations_language`
  FOREIGN KEY (`language`) REFERENCES `languages` (`alias`);

SET FOREIGN_KEY_CHECKS = 1;
