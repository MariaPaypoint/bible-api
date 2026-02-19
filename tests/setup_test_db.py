#!/usr/bin/env python3
"""
Скрипт инициализации тестовой БД cep_test.

Создаёт БД cep_test, применяет все миграции, загружает seed-данные.
Запуск внутри контейнера:
    python tests/setup_test_db.py
"""
import os
import sys
import re

# Пути проекта
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'app'))

# Устанавливаем DB_NAME до импорта app-модулей (чтобы config.py прочитал правильное значение)
os.environ["DB_NAME"] = "cep_test"

import mysql.connector
from mysql.connector import Error
from app.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD

TEST_DB_NAME = "cep_test"


def create_database():
    """Создаёт (пересоздаёт) тестовую БД"""
    print(f"Creating database {TEST_DB_NAME}...")
    conn = mysql.connector.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
    cursor.execute(
        f"CREATE DATABASE {TEST_DB_NAME} "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cursor.close()
    conn.close()
    print(f"Database {TEST_DB_NAME} created")


def run_migrations():
    """Применяет все миграции к тестовой БД"""
    print("Running migrations...")

    conn = mysql.connector.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD,
        database=TEST_DB_NAME
    )
    cursor = conn.cursor()

    # Отключаем FK — начальная миграция создаёт таблицы не в порядке FK-зависимостей
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    # Таблица учёта миграций
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            migration_name VARCHAR(255) NOT NULL UNIQUE,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_migration_name (migration_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    conn.commit()

    # Собираем файлы миграций
    migrations_dir = os.path.join(PROJECT_ROOT, 'migrations')
    migration_files = sorted([
        f for f in os.listdir(migrations_dir)
        if f.endswith('.sql') and re.match(r'^\d{4}_\d{2}_\d{2}_\d{6}_.*\.sql$', f)
    ])

    applied = 0
    for migration_file in migration_files:
        filepath = os.path.join(migrations_dir, migration_file)
        with open(filepath, 'r', encoding='utf-8') as f:
            sql = f.read()

        # Убираем хардкод имени БД из старых миграций
        sql = sql.replace('`bible_pause`.', '')
        sql = sql.replace('`cep`.', '')

        # Production использует utf8mb3, где varchar(10000) помещается в лимит строки.
        # При utf8mb4 два varchar(10000) дают >65535 байт → заменяем на text.
        sql = sql.replace('varchar(10000)', 'text')

        # Разделяем на отдельные SQL-операторы
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        for stmt in statements:
            # Пропускаем строки, состоящие только из комментариев
            non_comment = '\n'.join(
                line for line in stmt.split('\n')
                if line.strip() and not line.strip().startswith('--')
            )
            if not non_comment.strip():
                continue
            try:
                cursor.execute(stmt)
            except Error as e:
                # Некритичные ошибки: дубликат индекса, колонка уже существует и т.п.
                print(f"  Warning in {migration_file}: {e}")

        # Записываем миграцию как выполненную
        cursor.execute(
            "INSERT INTO migrations (migration_name) VALUES (%s)",
            (migration_file,)
        )
        conn.commit()
        applied += 1

    # Включаем FK обратно
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()

    cursor.close()
    conn.close()
    print(f"Applied {applied} migrations")


def load_seed_data():
    """Загружает seed-данные из SQL-файла"""
    print("Loading seed data...")

    seed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seed_test_data.sql')
    if not os.path.exists(seed_file):
        print(f"Seed file not found: {seed_file}")
        sys.exit(1)

    with open(seed_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    conn = mysql.connector.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD,
        database=TEST_DB_NAME
    )
    cursor = conn.cursor()

    statements = [s.strip() for s in sql.split(';') if s.strip()]
    for stmt in statements:
        non_comment = '\n'.join(
            line for line in stmt.split('\n')
            if line.strip() and not line.strip().startswith('--')
        )
        if not non_comment.strip():
            continue
        try:
            cursor.execute(stmt)
        except Error as e:
            print(f"  Error loading seed data: {e}")
            print(f"  Statement: {stmt[:200]}...")
            sys.exit(1)

    conn.commit()
    cursor.close()
    conn.close()
    print("Seed data loaded")


def main():
    create_database()
    run_migrations()
    load_seed_data()
    print(f"\nTest database {TEST_DB_NAME} is ready!")
    print("Run tests: pytest tests/ -v")


if __name__ == "__main__":
    main()
