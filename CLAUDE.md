# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bible API — a FastAPI REST API for managing Bible translations with audio support, word-level audio alignment, anomaly detection, and administrative controls. Documentation and comments are primarily in Russian.

## Common Commands

### Run / Build
```bash
docker compose up -d --build                    # Start (dev mode via compose command override)
docker logs bible-api -f                        # View logs
docker compose down                             # Stop
```

### Tests
```bash
# Unit tests only (safe, uses mocks, no DB)
pytest tests/ -k "not integration" -v

# All tests (integration tests hit real DB at localhost:8000)
pytest tests/ -v

# Single test file
pytest tests/test_excerpt.py -v

# Single test
pytest tests/test_excerpt.py::test_function_name -v
```

Integration tests (`test_*_integration.py`) make real HTTP requests to `localhost:8000` and use the DB from `app/config.py`. Unit tests use `@patch` mocks.

### Migrations
```bash
python migrate.py migrate              # Run pending migrations
python migrate.py create "name"        # Create new migration file
python migrate.py status               # Show migration status
python migrate.py mark-executed "f.sql" # Mark as already applied
```

Migration files live in `migrations/` with naming `YYYY_MM_DD_HHMMSS_name.sql`.

### OpenAPI Spec
```bash
docker exec bible-api bash -c "cd /code && PYTHONPATH=app python3 extract-openapi.py app.main:app"
```

## Architecture

### Application Structure (`app/`)

- **`main.py`** — FastAPI app entry point, all admin endpoints (anomalies, translations, voices, cache), the `timed_cache` decorator, and Swagger tag ordering. Imports routers from excerpt, checks, audio.
- **`excerpt.py`** — Core content endpoints: `chapter_with_alignment` and `excerpt_with_alignment`. Handles flexible verse reference parsing (e.g. "jhn 3:16-17"), audio alignment with manual fix overrides, and `lru_cache` for audio file existence checks.
- **`audio.py`** — MP3 file serving with HTTP Range request support. Accepts API key via query param (for HTML `<audio>` elements that can't send headers).
- **`auth.py`** — Two-level auth: static API key (`X-API-Key` header) for public GET endpoints (`RequireAPIKey`), JWT Bearer tokens for admin POST/PUT/PATCH endpoints (`RequireJWT`).
- **`models.py`** — Pydantic response/request models.
- **`database.py`** — MySQL connection factory via `create_connection()`. Returns a new connection each call; callers must close it.
- **`config.py`** — Environment variable loading. `API_KEY` and `JWT_SECRET_KEY` are required (will raise on startup if missing).
- **`checks.py`** — DB integrity check endpoints (verse counts, voice alignment validation).

### Key Patterns

**Database access** — no ORM. Raw SQL with `mysql-connector-python`. Pattern:
```python
connection = create_connection()
cursor = connection.cursor(dictionary=True)
try:
    cursor.execute(sql, params)
    results = cursor.fetchall()
    connection.commit()
finally:
    cursor.close()
    connection.close()
```

**Manual fixes override alignments** — `voice_manual_fixes` table takes priority over `voice_alignments` via `COALESCE(vmf.begin, a.begin)` in excerpt SQL queries.

**Caching** — Two mechanisms: `@timed_cache(seconds=3600)` (TTL-based dict cache in `main.py`) and `@lru_cache` (for audio file checks in `excerpt.py`). Both cleared via `POST /api/cache/clear`.

**Auth dependencies** — Use `RequireAPIKey = Depends(verify_api_key)` for public endpoints, `RequireJWT = Depends(verify_jwt_token)` for admin endpoints.

**Anomaly status workflow** — `detected` → `confirmed`/`disproved`/`corrected`/`disproved_whisper`. Status `corrected` requires `begin`/`end` timing values. Cannot revert from `corrected` to `confirmed`/`disproved`.

### Audio File Layout
```
{AUDIO_DIR}/{translation_alias}/{voice_alias}/mp3/{book_zerofill}/{chapter_zerofill}.mp3
```
Link templates in the `voices` table use placeholders: `{book_zerofill}`, `{chapter_zerofill}`, `{chapter_zerofill3}`, `{book}`, `{chapter}`, `{book_alias}`.

### Environment

Required env vars: `API_KEY`, `JWT_SECRET_KEY`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `AUDIO_DIR` (host path), `MP3_FILES_PATH` (container path). See `.env.example` for full list.

### All API routes are under `/api` prefix

Public (API Key): languages, translations, books, chapter/excerpt with alignment, audio streaming.
Admin (JWT): anomaly CRUD, manual fixes, translation/voice updates, cache clear, integrity checks.
