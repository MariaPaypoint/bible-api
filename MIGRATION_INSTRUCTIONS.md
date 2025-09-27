# Инструкции по применению миграций для voice_alignments

## Обзор изменений

Таблица `voice_alignments` была модифицирована для добавления полей `book_number`, `chapter_number` и `verse_number` для упрощения запросов и улучшения производительности.

## Созданные миграции

1. **2025_09_21_174716_add_book_chapter_verse_fields_to_voice_alignments.sql**
   - Добавляет новые поля: `book_number`, `chapter_number`, `verse_number`
   - Создает индексы для оптимизации производительности

2. **2025_09_21_174717_populate_book_chapter_verse_fields_in_voice_alignments.sql**
   - Заполняет новые поля данными из связанных таблиц `translation_verses` и `translation_books`

## Применение миграций

### Вариант 1: Через менеджер миграций (если зависимости установлены)
```bash
cd /root/cep/bible-api
python migrations/migration_manager.py migrate
```

### Вариант 2: Ручное применение SQL
```bash
# Применить первую миграцию
mysql -u username -p database_name < migrations/2025_09_21_174716_add_book_chapter_verse_fields_to_voice_alignments.sql

# Применить вторую миграцию
mysql -u username -p database_name < migrations/2025_09_21_174717_populate_book_chapter_verse_fields_in_voice_alignments.sql
```

## Изменения в коде

### Обновленные файлы:
- `app/main.py` - обновлены JOIN запросы для voice_alignments
- `app/excerpt.py` - обновлен запрос для получения выравниваний
- `app/checks.py` - обновлены проверки для использования новых полей

### Ключевые изменения:
- Заменены JOIN по `translation_verse` на прямые сравнения по `book_number`, `chapter_number`, `verse_number`
- Поле `translation_verse` сохранено для обратной совместимости
- Добавлены индексы для оптимизации производительности

## Преимущества новой структуры

1. **Упрощение запросов**: Прямое сравнение полей вместо сложных JOIN
2. **Улучшение производительности**: Индексы по новым полям
3. **Обратная совместимость**: Поле `translation_verse` сохранено
4. **Читаемость кода**: Более понятные условия в WHERE

## Проверка после применения

После применения миграций рекомендуется:

1. Проверить, что все записи в `voice_alignments` имеют заполненные новые поля:
```sql
SELECT COUNT(*) FROM voice_alignments WHERE book_number = 0 OR chapter_number = 0 OR verse_number = 0;
```

2. Убедиться, что индексы созданы:
```sql
SHOW INDEX FROM voice_alignments;
```

3. Запустить тесты приложения для проверки корректности работы.
