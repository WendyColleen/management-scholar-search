from __future__ import annotations

import time

from apscheduler.schedulers.background import BackgroundScheduler

from .db import init_db
from .ingest import ingest_once
from .config import settings


def main() -> None:
    init_db()

    scheduler = BackgroundScheduler(timezone=settings.timezone)
    # Pull new items every 6 hours
    scheduler.add_job(ingest_once, "interval", hours=6, kwargs={"limit_per_source": 40})
    scheduler.start()

    # First run right away
    ingest_once(limit_per_source=40)

    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
