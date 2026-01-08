from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Iterable, Tuple

import feedparser
import yaml
from sqlmodel import select

from .config import settings
from .db import get_session, init_db
from .models import Item
from .tagging import infer_tags
from .ai import summarize_with_openai

SOURCES_FILE = Path(__file__).parent / "sources" / "sources.yaml"


def _fingerprint(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def load_sources() -> list[dict]:
    data = yaml.safe_load(SOURCES_FILE.read_text(encoding="utf-8")) or {}
    return data.get("sources", [])

def _parse_date(entry) -> datetime | None:
    # feedparser may give struct_time in different fields
    for key in ("published_parsed", "updated_parsed"):
        st = getattr(entry, key, None)
        if st:
            try:
                return datetime(*st[:6])
            except Exception:
                pass
    return None


def iter_feed_items(
    source_name: str,
    feed_url: str,
    fallback_region: str,
    fallback_type: str,
) -> Iterable[Tuple[str, str, datetime | None, str, str, str, str]]:
    feed = feedparser.parse(feed_url)
    for e in feed.entries or []:
        title = (getattr(e, "title", "") or "").strip()
        url = (getattr(e, "link", "") or "").strip()
        if not title or not url:
            continue

        published = _parse_date(e)
        summary_text = (getattr(e, "summary", "") or "").strip()

        tags = infer_tags(title, summary_text, fallback_region=fallback_region, fallback_type=fallback_type)

        # optional AI summary (short)
        ai_sum = summarize_with_openai(title, summary_text) or ""

        yield title, url, published, tags.region, tags.item_type, tags.topic, (ai_sum or summary_text[:280])


def ingest_once(limit_per_source: int = 40) -> dict:
    init_db()
    sources = load_sources()
    inserted = 0
    skipped = 0

    with get_session() as session:
        for s in sources:
            name = s.get("name", "Unknown")
            url = s.get("url", "")
            if not url:
                continue
            fallback_region = s.get("default_region", "Global")
            fallback_type = s.get("default_type", "other")

            count = 0
            for title, link, published, region, item_type, topic, summary in iter_feed_items(name, url, fallback_region, fallback_type):
                count += 1
                if count > limit_per_source:
                    break

                fp = _fingerprint(link)
                existing = session.exec(select(Item).where(Item.fingerprint == fp)).first()
                if existing is not None:
                    skipped += 1
                    continue

                item = Item(
                    title=title,
                    url=link,
                    source=name,
                    published=published,
                    region=region,
                    item_type=item_type,
                    topic=topic,
                    summary=summary,
                    fingerprint=fp,
                )
                session.add(item)
                inserted += 1

        session.commit()

    return {"inserted": inserted, "skipped": skipped, "sources": len(sources)}
