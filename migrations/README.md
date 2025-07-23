# Database Migrations

Система миграций для Bible API, позволяющая управлять изменениями схемы базы данных.

## Использование

### Запуск миграций
```bash
python migrate.py migrate
```

### Создание новой миграции
```bash
python migrate.py create "migration_name"
```

### Просмотр статуса миграций
```bash
python migrate.py status
```

### Откат миграции (только запись в таблице)
```bash
python migrate.py rollback "migration_file.sql"
```

### Пометить миграцию как выполненную (для существующих БД)
```bash
python migrate.py mark-executed "migration_file.sql"
```

## Структура

- `migration_manager.py` - основной класс для управления миграциями
- `migrations/` - папка с файлами миграций
- `migrate.py` - CLI инструмент для управления миграциями

## Формат файлов миграций

Файлы миграций имеют формат: `YYYY_MM_DD_HHMMSS_migration_name.sql`

Пример:
```sql
-- Migration: create_users_table
-- Created: 2025-07-23 23:12:32

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_users_email ON users(email);
```

## Таблица миграций

Система автоматически создает таблицу `migrations` для отслеживания выполненных миграций:

```sql
CREATE TABLE migrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_migration_name (migration_name)
);
```

## Важные замечания

1. Каждое SQL-выражение должно заканчиваться точкой с запятой
2. Миграции выполняются в алфавитном порядке по имени файла
3. Откат миграции только удаляет запись из таблицы migrations - схему нужно откатывать вручную
4. Рекомендуется делать резервную копию базы данных перед выполнением миграций

## Для существующих баз данных

Если вы внедряете систему миграций в существующий проект с уже созданной схемой базы данных:

1. Создайте первую миграцию с дампом текущей структуры
2. Пометьте её как выполненную: `python migrate.py mark-executed "migration_file.sql"`
3. Теперь все новые миграции будут выполняться нормально
