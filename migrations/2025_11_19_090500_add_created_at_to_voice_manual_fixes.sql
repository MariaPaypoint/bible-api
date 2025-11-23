-- Migration: add_created_at_to_voice_manual_fixes
-- Created: 2025-11-19 09:05:00

-- Add created_at column to voice_manual_fixes table

ALTER TABLE `voice_manual_fixes` 
ADD COLUMN `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp';
