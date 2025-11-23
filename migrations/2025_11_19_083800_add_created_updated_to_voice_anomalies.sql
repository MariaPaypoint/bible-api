-- Migration: add_created_updated_to_voice_anomalies
-- Created: 2025-11-19 08:38:00

-- Add created_at and updated_at columns to voice_anomalies table

ALTER TABLE `voice_anomalies` 
ADD COLUMN `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
ADD COLUMN `updated_at` TIMESTAMP DEFAULT NULL COMMENT 'Record update timestamp';
