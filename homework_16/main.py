from __future__ import annotations

import asyncio
import logging
import os
import re
import signal
import sys
import time
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

import aiohttp
import aiosqlite
from bs4 import BeautifulSoup

HN_FRONT = "https://news.ycombinator.com/"
HN_ITEM = "https://news.ycombinator.com/item?id={id}"

USER_AGENT = (
    "HNAsyncCrawler/1.0 (+https://news.ycombinator.com/) "
    "Python aiohttp; contact=example@example.com"
)

logger = logging.getLogger("hn_crawler")


@dataclass
class Story:
    hn_id: int
    title: str
    url: Optional[str]
    author: Optional[str]
    points: Optional[int]
    num_comments: Optional[int]


async def init_db(db_path: str) -> aiosqlite.Connection:
    conn = await aiosqlite.connect(db_path)
    await conn.execute("PRAGMA journal_mode=WAL;")
    await conn.execute("PRAGMA synchronous=NORMAL;")
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY,
            hn_id INTEGER UNIQUE,
            title TEXT,
            url TEXT,
            author TEXT,
            points INTEGER,
            num_comments INTEGER,
            created_at INTEGER DEFAULT (strftime('%s','now')),
            fetched_at INTEGER
        )
        """
    )
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS discussion_links (
            id INTEGER PRIMARY KEY,
            hn_id INTEGER,
            link_url TEXT,
            link_text TEXT,
            created_at INTEGER DEFAULT (strftime('%s','now')),
            UNIQUE(hn_id, link_url)
        )
        """
    )
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fetch_runs (
            id INTEGER PRIMARY KEY,
            started_at INTEGER,
            finished_at INTEGER,
            status TEXT,
            note TEXT
        )
        """
    )
    await conn.commit()
    return conn


async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    for attempt in range(4):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                resp.raise_for_status()
                return await resp.text()
        except Exception as e:
            if attempt == 3:
                raise
            await asyncio.sleep(1.5 * (attempt + 1))
    return ""


def parse_front(html: str, top_n: int) -> List[Story]:
    soup = BeautifulSoup(html, "lxml")
    stories: List[Story] = []

    for athing in soup.select("tr.athing"):
        try:
            hn_id = int(athing.get("id"))
        except (TypeError, ValueError):
            continue

        title_a = athing.select_one("span.titleline a")
        title = title_a.get_text(strip=True) if title_a else ""
        url = title_a.get("href") if title_a else None

        subtext_tr = athing.find_next_sibling("tr")
        sub = subtext_tr.select_one("td.subtext") if subtext_tr else None

        author = None
        points = None
        num_comments = None

        if sub:
            user_a = sub.select_one("a.hnuser")
            author = user_a.get_text(strip=True) if user_a else None

            score_span = sub.select_one("span.score")
            if score_span:
                m = re.search(r"(\d+)", score_span.get_text(" "))
                if m:
                    points = int(m.group(1))
            links = sub.select("a")
            if links:
                last_a = links[-1]
                if last_a and "comment" in last_a.get_text(" "):
                    m2 = re.search(r"(\d+)", last_a.get_text(" "))
                    if m2:
                        num_comments = int(m2.group(1))

        stories.append(Story(hn_id=hn_id, title=title, url=url, author=author, points=points, num_comments=num_comments))

        if len(stories) >= top_n:
            break

    return stories


def extract_discussion_links(html: str) -> List[Tuple[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    links: List[Tuple[str, str]] = []

    for a in soup.select("table.fatitem a[href]"):
        href = a.get("href", "").strip()
        if href.startswith("item?id="):
            continue
        if href.startswith("http://") or href.startswith("https://"):
            links.append((href, a.get_text(strip=True)))

    for a in soup.select(".comment-tree span.commtext a[href]"):
        href = a.get("href", "").strip()
        if href.startswith("http://") or href.startswith("https://"):
            links.append((href, a.get_text(strip=True)))

    seen: Set[str] = set()
    deduped: List[Tuple[str, str]] = []
    for url, text in links:
        if url not in seen:
            seen.add(url)
            deduped.append((url, text))

    return deduped


async def upsert_story(conn: aiosqlite.Connection, story: Story) -> None:
    await conn.execute(
        """
        INSERT INTO stories (hn_id, title, url, author, points, num_comments, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, strftime('%s','now'))
        ON CONFLICT(hn_id) DO UPDATE SET
            title=excluded.title,
            url=excluded.url,
            author=excluded.author,
            points=excluded.points,
            num_comments=excluded.num_comments,
            fetched_at=excluded.fetched_at
        """,
        (story.hn_id, story.title, story.url, story.author, story.points, story.num_comments),
    )


async def insert_discussion_links(conn: aiosqlite.Connection, hn_id: int, links: List[Tuple[str, str]]) -> None:
    await conn.executemany(
        """
        INSERT OR IGNORE INTO discussion_links (hn_id, link_url, link_text)
        VALUES (?, ?, ?)
        """,
        [(hn_id, url, text) for url, text in links],
    )


async def process_story(
    session: aiohttp.ClientSession,
    conn: aiosqlite.Connection,
    story: Story,
    sem: asyncio.Semaphore,
) -> None:
    async with sem:
        try:
            html = await fetch(session, HN_ITEM.format(id=story.hn_id))
            links = extract_discussion_links(html)
            await upsert_story(conn, story)
            await insert_discussion_links(conn, story.hn_id, links)
            logger.info("Saved story %s (%d links)", story.hn_id, len(links))
        except Exception:
            logger.exception("Failed to process story %s", story.hn_id)


async def run_once(conn: aiosqlite.Connection, session: aiohttp.ClientSession, top_n: int, concurrency: int) -> None:
    run_id = None
    started = int(time.time())
    try:
        cur = await conn.execute(
            "INSERT INTO fetch_runs (started_at, status) VALUES (?, ?)", (started, "running")
        )
        await conn.commit()
        run_id = cur.lastrowid

        front_html = await fetch(session, HN_FRONT)
        stories = parse_front(front_html, top_n)
        logger.info("Found %d front-page stories", len(stories))

        sem = asyncio.Semaphore(concurrency)
        tasks = [process_story(session, conn, s, sem) for s in stories]
        await asyncio.gather(*tasks)

        await conn.execute(
            "UPDATE fetch_runs SET finished_at=?, status=? WHERE id=?",
            (int(time.time()), "ok", run_id),
        )
        await conn.commit()
    except Exception as e:
        logger.exception("Run failed")
        if run_id is not None:
            await conn.execute(
                "UPDATE fetch_runs SET finished_at=?, status=?, note=? WHERE id=?",
                (int(time.time()), "error", str(e), run_id),
            )
            await conn.commit()


async def periodic(interval: int, db_path: str, top_n: int, concurrency: int) -> None:
    conn = await init_db(db_path)

    timeout = aiohttp.ClientTimeout(total=30)
    headers = {"User-Agent": USER_AGENT}

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        stop_event = asyncio.Event()

        def _handle_sig():
            logger.info("Shutdown signal received")
            stop_event.set()

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _handle_sig)
            except NotImplementedError:
                signal.signal(sig, lambda *_: stop_event.set())

        while not stop_event.is_set():
            started_at = time.time()
            await run_once(conn, session, top_n, concurrency)
            elapsed = time.time() - started_at
            sleep_for = max(0.0, interval - elapsed)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=sleep_for)
            except asyncio.TimeoutError:
                pass

    await conn.close()


def parse_args(argv: List[str]) -> Tuple[int, str, int, int]:
    import argparse

    parser = argparse.ArgumentParser(description="Async Hacker News crawler")
    parser.add_argument("--interval", type=int, default=int(os.getenv("HN_INTERVAL", 300)), help="интервал повторения в секундах")
    parser.add_argument("--db", type=str, default=os.getenv("HN_DB", "hn.db"), help="путь к SQLite базе")
    parser.add_argument("--top-n", type=int, default=int(os.getenv("HN_TOP_N", 30)), help="число новостей с главной страницы")
    parser.add_argument("--concurrency", type=int, default=int(os.getenv("HN_CONCURRENCY", 8)), help="число одновременных запросов")
    parser.add_argument("--log-level", type=str, default=os.getenv("HN_LOG_LEVEL", "INFO"), help="уровень логгирования")

    ns = parser.parse_args(argv)
    return ns.interval, ns.db, ns.top_n, ns.concurrency, ns.log_level


def setup_logging(level: str) -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def amain(argv: List[str]) -> int:
    interval, db_path, top_n, concurrency, log_level = parse_args(argv)
    setup_logging(log_level)
    logger.info("Starting HN crawler: interval=%ss top_n=%s concurrency=%s db=%s", interval, top_n, concurrency, db_path)
    await periodic(interval=interval, db_path=db_path, top_n=top_n, concurrency=concurrency)
    return 0


def main() -> None:
    try:
        asyncio.run(amain(sys.argv[1:]))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
