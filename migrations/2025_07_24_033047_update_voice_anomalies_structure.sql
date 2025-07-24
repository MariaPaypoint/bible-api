-- Migration: update_voice_anomalies_structure
-- Created: 2025-07-24 03:30:47

-- Update voice_anomalies table structure
-- Make verse_number NOT NULL, word nullable, duration/speed nullable, anomaly_type NOT NULL

ALTER TABLE `voice_anomalies` 
CHANGE COLUMN `verse_number` `verse_number` SMALLINT NOT NULL,
CHANGE COLUMN `word` `word` VARCHAR(100) NULL,
CHANGE COLUMN `duration` `duration` DECIMAL(7,3) NULL,
CHANGE COLUMN `speed` `speed` DECIMAL(7,2) NULL,
CHANGE COLUMN `anomaly_type` `anomaly_type` VARCHAR(30) NOT NULL;

-- Example:
-- CREATE TABLE example_table (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     name VARCHAR(255) NOT NULL
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
