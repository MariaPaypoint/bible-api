#!/usr/bin/env python3
"""Download MP3 audio files for active voices.

This script reads `voices.link_template` for all active voices (and active translations)
from the configured MySQL database and downloads per-chapter mp3 files into the
expected folder structure:

  <output_root>/<translation_alias>/<voice_alias>/mp3/<book_zerofill>/<chapter_zerofill>.mp3

The URL for each chapter is built by replacing `{placeholders}` in `link_template`
(similar to `/root/cep/php-parser/include.php:get_chapter_audio_url`).

Designed to be executed inside the `bible-api` container where DB_*/API config is
already available via `.env`.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import mysql.connector
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass(frozen=True)
class Voice:
    voice_code: int
    voice_alias: str
    translation_code: int
    translation_alias: str
    link_template: str


@dataclass(frozen=True)
class Book:
    number: int
    code1: str
    code2: str
    code3: str
    code4: str
    code5: str
    code6: str
    code7: str
    code8: str
    code9: str


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _mysql_connect():
    host = os.getenv("DB_HOST", "localhost")
    port = _env_int("DB_PORT", 3306)
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "cep")

    return mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        autocommit=True,
    )


def _fetch_active_voices(conn) -> List[Voice]:
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT
            v.code AS voice_code,
            v.alias AS voice_alias,
            v.translation AS translation_code,
            t.alias AS translation_alias,
            v.link_template AS link_template
        FROM voices v
        JOIN translations t ON t.code = v.translation
        WHERE v.active = 1 AND t.active = 1
        ORDER BY t.alias, v.alias
        """
    )
    rows = cur.fetchall()
    cur.close()

    voices: List[Voice] = []
    for r in rows:
        tmpl = (r.get("link_template") or "").strip()
        voices.append(
            Voice(
                voice_code=int(r["voice_code"]),
                voice_alias=str(r["voice_alias"]),
                translation_code=int(r["translation_code"]),
                translation_alias=str(r["translation_alias"]),
                link_template=tmpl,
            )
        )
    return voices


def _fetch_books(conn) -> Dict[int, Book]:
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT number, code1, code2, code3, code4, code5, code6, code7, code8, code9
        FROM bible_books
        ORDER BY number
        """
    )
    rows = cur.fetchall()
    cur.close()

    out: Dict[int, Book] = {}
    for r in rows:
        out[int(r["number"])] = Book(
            number=int(r["number"]),
            code1=str(r.get("code1") or ""),
            code2=str(r.get("code2") or ""),
            code3=str(r.get("code3") or ""),
            code4=str(r.get("code4") or ""),
            code5=str(r.get("code5") or ""),
            code6=str(r.get("code6") or ""),
            code7=str(r.get("code7") or ""),
            code8=str(r.get("code8") or ""),
            code9=str(r.get("code9") or ""),
        )
    return out


def _fetch_chapter_counts(conn) -> Dict[int, int]:
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT book_number, MAX(chapter_number) AS chapter_count
        FROM bible_stat
        GROUP BY book_number
        """
    )
    rows = cur.fetchall()
    cur.close()

    out: Dict[int, int] = {}
    for r in rows:
        out[int(r["book_number"])] = int(r["chapter_count"])
    return out


def _simple_template_replace(template: str, variables: Dict[str, Any]) -> str:
    out = template
    for k, v in variables.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def _build_url(voice: Voice, book: Book, chapter: int) -> str:
    book_number = book.number
    book_zerofill = str(book_number).zfill(2)
    chapter_zerofill = str(chapter).zfill(2)

    vars_map = {
        "voice": voice.voice_alias,
        "book": book_number,
        "chapter": chapter,
        "book_zerofill": book_zerofill,
        "chapter_zerofill": chapter_zerofill,
        "chapter_zerofill3": str(chapter).zfill(3),
        "chapter_zerofill_ps3": str(chapter).zfill(3 if book_number == 19 else 2),
        "book_alias": book.code1,
        "translation": voice.translation_alias,
        "book_alias_upper": book.code1.upper(),
        "book_code2": book.code2,
        "book_code3": book.code3,
        "book_code4": book.code4,
        "book_code5": book.code5,
        "book_code6": book.code6,
        "book_code7": book.code7,
        "book_code8": book.code8,
        "book_code9": book.code9,
    }

    return _simple_template_replace(voice.link_template, vars_map)


def _dest_path(output_root: Path, voice: Voice, book_number: int, chapter: int) -> Path:
    book0 = str(book_number).zfill(2)
    chapter0 = str(chapter).zfill(2)
    return output_root / voice.translation_alias / voice.voice_alias / "mp3" / book0 / f"{chapter0}.mp3"


def _requests_session(user_agent: str, retries: int, backoff: float) -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=32, pool_maxsize=32)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({"User-Agent": user_agent, "Accept": "audio/mpeg,*/*"})
    return s


def _looks_like_mp3(first_bytes: bytes) -> bool:
    # ID3 tag or frame sync 0xFFEx
    return first_bytes.startswith(b"ID3") or (len(first_bytes) >= 2 and first_bytes[0] == 0xFF and (first_bytes[1] & 0xE0) == 0xE0)


def _download_one(
    session: requests.Session,
    url: str,
    dest: Path,
    timeout: float,
    dry_run: bool,
    skip_existing: bool,
) -> Tuple[bool, str]:
    if skip_existing and dest.exists() and dest.stat().st_size > 0:
        return True, "exists"

    if dry_run:
        return True, "dry-run"

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")

    r = session.get(url, stream=True, timeout=timeout, allow_redirects=True)
    if r.status_code != 200:
        return False, f"http {r.status_code}"

    # Basic sanity check: make sure we are not saving HTML error pages.
    it = r.iter_content(chunk_size=64 * 1024)
    try:
        first = next(it)
    except StopIteration:
        return False, "empty"

    if not _looks_like_mp3(first[:16]):
        ct = (r.headers.get("Content-Type") or "").lower()
        return False, f"not-mp3 content-type={ct!r}"

    with open(tmp, "wb") as f:
        f.write(first)
        for chunk in it:
            if not chunk:
                continue
            f.write(chunk)

    os.replace(tmp, dest)
    return True, "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description="Download mp3 files for all active voices (voices.active=1 AND translations.active=1).")
    ap.add_argument("--output-root", default=os.getenv("MP3_FILES_PATH", "/audio"), help="Root dir for mp3 storage (default: MP3_FILES_PATH env or /audio).")
    ap.add_argument("--max-workers", type=int, default=8, help="Concurrent downloads (default: 8).")
    ap.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout in seconds (default: 30).")
    ap.add_argument("--retries", type=int, default=5, help="Retry count for network/http errors (default: 5).")
    ap.add_argument("--backoff", type=float, default=0.5, help="Retry backoff factor (default: 0.5).")
    ap.add_argument("--user-agent", default="bible-api-audio-downloader/1.0", help="HTTP User-Agent.")
    ap.add_argument("--translation-alias", action="append", default=[], help="Filter by translation alias (repeatable).")
    ap.add_argument("--voice-alias", action="append", default=[], help="Filter by voice alias (repeatable).")
    ap.add_argument("--dry-run", action="store_true", help="Do not download, only print planned actions.")
    ap.add_argument("--no-skip-existing", action="store_true", help="Re-download even if destination file exists.")
    ap.add_argument("--yes", action="store_true", help="Required to actually download (safety flag).")
    args = ap.parse_args()

    output_root = Path(args.output_root).resolve()
    skip_existing = not args.no_skip_existing

    if not args.dry_run and not args.yes:
        print("Refusing to run without --yes (this may download tens of GB). Use --dry-run to preview.")
        return 2

    conn = _mysql_connect()
    try:
        voices = _fetch_active_voices(conn)
        books = _fetch_books(conn)
        chapter_counts = _fetch_chapter_counts(conn)
    finally:
        conn.close()

    if args.translation_alias:
        allow = set(args.translation_alias)
        voices = [v for v in voices if v.translation_alias in allow]

    if args.voice_alias:
        allow = set(args.voice_alias)
        voices = [v for v in voices if v.voice_alias in allow]

    # Skip voices without templates.
    voices_no_template = [v for v in voices if not v.link_template]
    voices = [v for v in voices if v.link_template]

    if voices_no_template:
        print("Skipping voices without link_template:")
        for v in voices_no_template:
            print(f"  - {v.translation_alias}/{v.voice_alias} (voice_code={v.voice_code})")

    total_tasks = 0
    for v in voices:
        total_tasks += sum(chapter_counts.get(bn, 0) for bn in chapter_counts.keys())

    print(f"Output root: {output_root}")
    print(f"Voices: {len(voices)}")
    print(f"Planned chapter downloads (upper bound): {total_tasks}")

    from concurrent.futures import ThreadPoolExecutor, as_completed

    session = _requests_session(args.user_agent, args.retries, args.backoff)

    ok = 0
    skipped = 0
    failed = 0

    start = time.time()

    def iter_jobs() -> Iterable[Tuple[str, Path]]:
        for v in voices:
            for book_number, max_ch in sorted(chapter_counts.items()):
                book = books.get(book_number)
                if not book:
                    continue
                for ch in range(1, max_ch + 1):
                    url = _build_url(v, book, ch)
                    dest = _dest_path(output_root, v, book_number, ch)
                    yield url, dest

    jobs = list(iter_jobs())

    if args.dry_run:
        for url, dest in jobs[:50]:
            print(f"DRY {url} -> {dest}")
        if len(jobs) > 50:
            print(f"... ({len(jobs)-50} more)")
        return 0

    print(f"Starting downloads with max_workers={args.max_workers}...")

    # Use a thread pool for IO-bound downloads.
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = {}
        for url, dest in jobs:
            fut = ex.submit(_download_one, session, url, dest, args.timeout, False, skip_existing)
            futs[fut] = (url, dest)

        last_report = 0.0
        for fut in as_completed(futs):
            url, dest = futs[fut]
            try:
                success, msg = fut.result()
            except Exception as e:
                success, msg = False, f"exc {type(e).__name__}: {e}"

            if success:
                if msg == "exists":
                    skipped += 1
                else:
                    ok += 1
            else:
                failed += 1
                print(f"FAIL {msg}: {url} -> {dest}")

            now = time.time()
            if now - last_report >= 10:
                done = ok + skipped + failed
                rate = done / max(1.0, now - start)
                print(f"Progress: done={done}/{len(jobs)} ok={ok} skipped={skipped} failed={failed} rate={rate:.1f}/s")
                last_report = now

    print(f"Finished: ok={ok} skipped={skipped} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
