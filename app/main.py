from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from .config import settings
from .db import init_db, get_session
from .models import Item
from .ingest import ingest_once
from .feed import build_rss
from .mailerlite import get_or_create_group, upsert_subscriber

app = FastAPI(title=settings.site_name)
templates = Jinja2Templates(directory=str((__import__("pathlib").Path(__file__).parent / "templates").resolve()))


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"ok": True, "time": datetime.utcnow().isoformat()}


@app.get("/admin/ingest")
def admin_ingest() -> dict:
    # convenience endpoint for you; protect later if you want
    return ingest_once(limit_per_source=40)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, region: str = "All", item_type: str = "All", q: str = ""):
    regions = ["All"] + settings.regions
    types = ["All", "funding", "cfp", "conference", "journal", "other"]

    stmt = select(Item).order_by(Item.published.desc().nullslast(), Item.fetched_at.desc())
    if region != "All":
        stmt = stmt.where(Item.region == region)
    if item_type != "All":
        stmt = stmt.where(Item.item_type == item_type)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where((Item.title.ilike(like)) | (Item.summary.ilike(like)) | (Item.topic.ilike(like)))

    with get_session() as session:
        items = session.exec(stmt.limit(120)).all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "items": items,
            "regions": regions,
            "types": types,
            "selected_region": region,
            "selected_type": item_type,
            "q": q,
            "settings": settings,
        },
    )


@app.get("/feeds/newsletter.xml")
def newsletter_feed(region: str = "All"):
    # Weekly digest feed (Mailerlite can consume this as an RSS campaign)
    since = datetime.utcnow() - timedelta(days=7)
    stmt = select(Item).where((Item.published == None) | (Item.published >= since)).order_by(
        Item.published.desc().nullslast(), Item.fetched_at.desc()
    )
    if region != "All":
        stmt = stmt.where(Item.region == region)

    with get_session() as session:
        items = session.exec(stmt.limit(50)).all()

    rss = build_rss(
        title=f"{settings.site_name} – Weekly Digest" + (f" ({region})" if region != "All" else ""),
        link=settings.public_base_url,
        description="Automatically curated academic opportunities and business research items.",
        items=items,
    )
    return Response(content=rss, media_type="application/rss+xml")


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, "settings": settings})


@app.post("/subscribe", response_class=HTMLResponse)
def subscribe(
    request: Request,
    email: str = Form(...),
    region: str = Form("All"),
):
    # Adds user to MailerLite group (one group per region)
    if region == "All":
        region = "Global"

    try:
        group_id = get_or_create_group(f"MSS – {region}")
        upsert_subscriber(email=email, group_ids=[group_id], fields={"region": region})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Subscription failed: {e}")

    return templates.TemplateResponse(
        "subscribed.html",
        {
            "request": request,
            "email": email,
            "region": region,
            "settings": settings,
        },
    )
