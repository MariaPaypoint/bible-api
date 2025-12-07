ALTER TABLE translation_titles
ADD COLUMN subtitle TINYINT(1) NOT NULL DEFAULT 0 AFTER reference,
ADD COLUMN position_text INT NULL AFTER subtitle,
ADD COLUMN position_html INT NULL AFTER position_text;
