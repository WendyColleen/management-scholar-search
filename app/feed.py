from __future__ import annotations

from datetime import datetime
from typing import Iterable
from xml.sax.saxutils import escape

from .models import Item


def _fmt(dt: datetime | None) -> str:
    if not dt:
        return ""
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")


def build_rss(title: str, link: str, description: str, items: Iterable[Item]) -> str:
    now = datetime.utcnow()
    self_link = link.rstrip("/") + "/feeds/newsletter.xml"
    parts = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append('<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">')
    parts.append("<channel>")
    parts.append(f"<title>{escape(title)}</title>")
    parts.append(f"<link>{escape(link)}</link>")
    parts.append(f"<description>{escape(description)}</description>")
    parts.append(f"<lastBuildDate>{_fmt(now)}</lastBuildDate>")
    parts.append(
        f'<atom:link href="{escape(self_link)}" rel="self" type="application/rss+xml" />'
    )

    for it in items:
        pub = it.published or it.fetched_at
        parts.append("<item>")
        parts.append(f"<title>{escape(it.title)}</title>")
        parts.append(f"<link>{escape(it.url)}</link>")
        parts.append(f"<guid isPermaLink=\"true\">{escape(it.url)}</guid>")
        parts.append(f"<pubDate>{_fmt(pub)}</pubDate>")
        summary = it.summary or ""
        meta = f"<p><b>Region:</b> {escape(it.region)} &nbsp; <b>Type:</b> {escape(it.item_type)} &nbsp; <b>Topic:</b> {escape(it.topic)}</p>"
        parts.append(f"<description><![CDATA[{meta}<p>{escape(summary)}</p>]]></description>")
        parts.append("</item>")

    parts.append("</channel>")
    parts.append("</rss>")
    return "\n".join(parts)
