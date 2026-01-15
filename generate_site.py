"""
ManagementScholarSearch static-site generator.

Run locally:
  py generate_site.py

It will:
  1) Ingest RSS sources into a local SQLite db (data/mss.sqlite)
  2) Generate a static site into ./docs/ (GitHub Pages)

Then publish by pushing to GitHub.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlmodel import select

from app.config import settings
from app.db import get_session, init_db
from app.feed import build_rss
from app.ingest import ingest_once
from app.models import Item

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"


def _load_env() -> None:
    """Load .env when running locally (so MAILERLITE_FORM_URL etc. are available)."""
    load_dotenv(dotenv_path=ROOT / ".env", override=False)


def _ensure_local_db_path() -> None:
    """Make sure DB_PATH points to a local file when generating."""
    if os.getenv("DB_PATH"):
        return
    # Default to local db (instead of Docker default /data/mss.sqlite)
    os.environ["DB_PATH"] = str((DATA_DIR / "mss.sqlite").resolve())


def _item_to_dict(it: Item) -> dict[str, Any]:
    dt = it.published or it.fetched_at
    return {
        "title": it.title,
        "url": it.url,
        "source": it.source,
        "date": dt.strftime("%Y-%m-%d"),
        "datetime": dt.isoformat(),
        "region": it.region,
        "item_type": it.item_type,
        "topic": it.topic,
        "summary": it.summary or "",
    }


def _render_index(items: list[dict[str, Any]]) -> str:
    # Minimal, fast, static UI with client-side filtering.
    regions = ["All"] + settings.regions

    # You said you do not want journal articles on the site.
    types = ["All", "funding", "cfp", "conference", "other"]

    # AdSense: script loads only if client id is set.
    ads_script = ""
    ad_slot = (settings.adsense_ad_slot or "").strip()
    if (settings.adsense_client_id or "").strip():
        ads_script = (
            f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={settings.adsense_client_id}" crossorigin="anonymous"></script>'
        )

    # Sidebar ad unit
    ad_box = ""
    if (settings.adsense_client_id or "").strip() and ad_slot:
        ad_box = f"""
        <div class="card mb-3">
          <div class="card-body">
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="{settings.adsense_client_id}"
                 data-ad-slot="{ad_slot}"
                 data-ad-format="auto"
                 data-full-width-responsive="true"></ins>
            <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
          </div>
        </div>
        """
    else:
        ad_box = """
        <div class="card mb-3">
          <div class="card-body small text-muted">
            <div class="fw-semibold">Ad slot</div>
            <div>Set <code>ADSENSE_CLIENT_ID</code> and <code>ADSENSE_AD_SLOT</code> in <code>.env</code>.</div>
          </div>
        </div>
        """

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Basic HTML with Bootstrap CDN. Filtering happens in JS using docs/assets/items.json.
    # Newsletter subscribe button is populated client-side from docs/assets/public_config.json
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{settings.site_name}</title>
    <meta name="description" content="Research funding, CFPs, and conferences in management & international business." />
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
    {ads_script}
    <style>
      body {{ background: #f7f7fb; }}
      .brand {{ letter-spacing: 0.2px; }}
      .item-card a {{ text-decoration: none; }}
      .badge {{ font-weight: 500; }}
    </style>
  </head>
  <body>
    <nav class="navbar navbar-expand-lg bg-white border-bottom">
      <div class="container py-1">
        <span class="navbar-brand fw-semibold brand">{settings.site_name}</span>
        <div class="ms-auto small text-muted">Updated: {generated_at}</div>
      </div>
    </nav>

    <main class="container my-4">
      <div class="row g-4">
        <div class="col-lg-9">
          <div class="card mb-3">
            <div class="card-body">
              <div class="row g-2 align-items-end">
                <div class="col-md-3">
                  <label class="form-label">Region</label>
                  <select class="form-select" id="regionSelect">
                    {''.join([f'<option value="{r}">{r}</option>' for r in regions])}
                  </select>
                </div>
                <div class="col-md-3">
                  <label class="form-label">Type</label>
                  <select class="form-select" id="typeSelect">
                    {''.join([f'<option value="{t}">{t}</option>' for t in types])}
                  </select>
                </div>
                <div class="col-md-6">
                  <label class="form-label">Search</label>
                  <input class="form-control" id="searchInput" placeholder="e.g., grant, fellowship, call for papers" />
                </div>
              </div>
            </div>
          </div>

          <div id="results" class="d-flex flex-column gap-3"></div>
          <div id="emptyState" class="alert alert-info d-none">No matching items.</div>
        </div>

        <div class="col-lg-3">
          <div class="card mb-3">
            <div class="card-body">
              <h6 class="fw-semibold">Free newsletter</h6>
              <p class="small text-muted mb-3">Weekly digest. Subscribe by region.</p>

              <div id="subscribeArea">
                <a id="subscribeBtn" class="btn btn-outline-primary w-100 d-none"
                   href="#" target="_blank" rel="noopener">Subscribe</a>

                <div id="subscribeHelp" class="small text-muted">
                  Add your MailerLite signup form link in <code>docs/assets/public_config.json</code>
                  as <code>"mailerlite_form_url"</code>.
                </div>
              </div>

              <hr>
              <div class="small">RSS feed: <a href="feeds/newsletter.xml">feeds/newsletter.xml</a></div>
            </div>
          </div>

          {ad_box}

          
    </main>

    <script>
      const state = {{ items: [], filtered: [] }};

      function norm(s) {{ return (s || '').toLowerCase(); }}

      // More forgiving matching to reduce "No matching items" caused by label variants.
      function matches(it, region, type, q) {{
        const itRegion = it.region || '';
        const itType = it.item_type || '';

        if (region !== 'All') {{
          const regionOk =
            itRegion === region ||
            (region === 'Europe' && (itRegion === 'EU' || itRegion === 'European Union')) ||
            (region === 'North America' && (itRegion === 'USA' || itRegion === 'United States' || itRegion === 'Canada'));
          if (!regionOk) return false;
        }}

        if (type !== 'All') {{
          const typeOk =
            itType === type ||
            (type === 'funding' && (itType === 'grant' || itType === 'call' || itType === 'cfp')) ||
            (type === 'cfp' && (itType === 'call'));
          if (!typeOk) return false;
        }}

        if (q) {{
          const hay = norm(it.title + ' ' + it.summary + ' ' + it.topic + ' ' + it.source);
          if (!hay.includes(q)) return false;
        }}
        return true;
      }}

      function render() {{
        const box = document.getElementById('results');
        box.innerHTML = '';
        const empty = document.getElementById('emptyState');
        if (!state.filtered.length) {{
          empty.classList.remove('d-none');
          return;
        }}
        empty.classList.add('d-none');

        for (const it of state.filtered) {{
          const card = document.createElement('div');
          card.className = 'card item-card';
          card.innerHTML = `
            <div class="card-body">
              <div class="d-flex justify-content-between flex-wrap gap-2">
                <h5 class="mb-1"><a href="${{it.url}}" target="_blank" rel="noopener">${{it.title}}</a></h5>
                <div class="small text-muted">${{it.date}} · ${{it.source}}</div>
              </div>
              <div class="small text-muted mb-2">
                <span class="badge text-bg-light border">${{it.region}}</span>
                <span class="badge text-bg-light border">${{it.item_type}}</span>
                <span class="badge text-bg-light border">${{it.topic}}</span>
              </div>
              ${{it.summary ? `<p class="mb-0">${{it.summary}}</p>` : ''}}
            </div>`;
          box.appendChild(card);
        }}
      }}

      function applyFilters() {{
        const region = document.getElementById('regionSelect').value;
        const type = document.getElementById('typeSelect').value;
        const q = norm(document.getElementById('searchInput').value.trim());
        state.filtered = state.items.filter(it => matches(it, region, type, q));
        render();
      }}

      async function loadPublicConfig() {{
        try {{
          const resp = await fetch('assets/public_config.json', {{ cache: 'no-store' }});
          if (!resp.ok) return;
          const cfg = await resp.json();
          const url = (cfg.mailerlite_form_url || '').trim();
          if (!url) return;

          const btn = document.getElementById('subscribeBtn');
          const help = document.getElementById('subscribeHelp');
          btn.href = url;
          btn.classList.remove('d-none');
          if (help) help.classList.add('d-none');
        }} catch (e) {{}}
      }}

      async function boot() {{
        await loadPublicConfig();

        const resp = await fetch('assets/items.json');
        state.items = await resp.json();

        // Funding-first default view
        const typeSel = document.getElementById('typeSelect');
        if (typeSel) typeSel.value = 'funding';

        applyFilters();

        document.getElementById('regionSelect').addEventListener('change', applyFilters);
        document.getElementById('typeSelect').addEventListener('change', applyFilters);
        document.getElementById('searchInput').addEventListener('input', applyFilters);
      }}

      boot();
    </script>
  </body>
</html>
"""


def _write_public_config() -> None:
    """
    Ensure docs/assets/public_config.json exists and is updated with MAILERLITE_FORM_URL from .env (if provided).
    This file is safe to commit: only public URLs go here.
    """
    cfg_path = DOCS_DIR / "assets" / "public_config.json"
    cfg: dict[str, Any] = {}

    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            if not isinstance(cfg, dict):
                cfg = {}
        except Exception:
            cfg = {}

    # Only set/override mailerlite_form_url if env provides it.
    ml = (os.getenv("MAILERLITE_FORM_URL") or "").strip()
    if ml:
        cfg["mailerlite_form_url"] = ml
    else:
        cfg.setdefault("mailerlite_form_url", "")

    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    _load_env()
    _ensure_local_db_path()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    init_db()

    # Pull fresh items
    result = ingest_once(limit_per_source=int(os.getenv("LIMIT_PER_SOURCE", "40")))
    print(f"Ingest complete: inserted={result['inserted']} skipped={result['skipped']} sources={result['sources']}")

    # Load recent items
    with get_session() as session:
        items = session.exec(
            select(Item).order_by(Item.fetched_at.desc()).limit(int(os.getenv("MAX_ITEMS", "500")))
        ).all()

    # Exclude journals from the public site entirely
    items_public = [it for it in items if (it.item_type or "").lower() != "journal"]
    items_dict = [_item_to_dict(it) for it in items_public]

    # Build RSS (newsletter) from non-journal items
    rss_items = items_public[: int(os.getenv("NEWSLETTER_ITEMS", "60"))]
    rss = build_rss(
        title=f"{settings.site_name} – Weekly Digest",
        link=settings.public_base_url.rstrip("/"),
        description="Research funding, CFPs, and conferences in management & international business.",
        items=rss_items,
    )

    # Write docs
    (DOCS_DIR / "assets").mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "feeds").mkdir(parents=True, exist_ok=True)

    (DOCS_DIR / "assets" / "items.json").write_text(
        json.dumps(items_dict, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DOCS_DIR / "feeds" / "newsletter.xml").write_text(rss, encoding="utf-8")
    (DOCS_DIR / "index.html").write_text(_render_index(items_dict), encoding="utf-8")

    _write_public_config()

    # GitHub Pages niceties
    (DOCS_DIR / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS_DIR / "CNAME").write_text(settings.domain_name.strip(), encoding="utf-8")

    print(f"Static site written to: {DOCS_DIR}")
    print('Next: commit/push the "docs/" folder (GitHub Desktop is fine).')


if __name__ == "__main__":
    main()
