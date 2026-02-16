-- Migration: add_disproved_whisper_to_voice_anomalies
-- Created: 2026-02-16

ALTER TABLE `voice_anomalies` MODIFY COLUMN `status`
  ENUM('detected','confirmed','disproved','corrected','already_resolved','disproved_whisper')
  NOT NULL DEFAULT 'detected';
