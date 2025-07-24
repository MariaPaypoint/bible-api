-- Migration: add_status_to_voice_anomalies
-- Created: 2025-07-23 23:45:39

-- Add status column to voice_anomalies table
-- Status values:
-- detected - ошибка выявлена (по умолчанию)
-- confirmed - ошибка подтверждена
-- disproved - ошибка опровергнута, не подтверждена проверкой
-- corrected - выполнена ручная коррекция
-- already_resolved - уже исправлена ранее

ALTER TABLE `voice_anomalies` 
ADD COLUMN `status` ENUM('detected', 'confirmed', 'disproved', 'corrected', 'already_resolved') 
NOT NULL DEFAULT 'detected' 
COMMENT 'Status of anomaly: detected, confirmed, disproved, corrected, already_resolved';

-- Add index for better performance when filtering by status
CREATE INDEX `idx_voice_anomalies_status` ON `voice_anomalies` (`status`);

-- Add composite index for voice + status filtering
CREATE INDEX `idx_voice_anomalies_voice_status` ON `voice_anomalies` (`voice`, `status`);
