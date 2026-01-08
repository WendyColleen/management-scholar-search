from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    val = os.getenv(name, default)
    return val.strip() if isinstance(val, str) else default


@dataclass(frozen=True)
class Settings:
    site_name: str = _env("SITE_NAME", "ManagementScholarSearch")
    domain_name: str = _env("DOMAIN_NAME", "managementscholarsearch.com")
    public_base_url: str = _env("PUBLIC_BASE_URL", "http://localhost:8000")
    regions_csv: str = _env("REGIONS", "North America,Europe,Asia,Global")
    timezone: str = _env("TIMEZONE", "Europe/Vienna")

    db_path: str = _env("DB_PATH", "/data/mss.sqlite")

    openai_api_key: str = _env("OPENAI_API_KEY", "")

    # MailerLite API token (new API uses Authorization: Bearer ...)
    email_api_key: str = _env("EMAIL_API_KEY", "")

    # Google AdSense pub id, e.g., ca-pub-...
    adsense_client_id: str = _env("ADSENSE_CLIENT_ID", "")
    adsense_ad_slot: str = _env("ADSENSE_AD_SLOT", "")

    newsletter_day: str = _env("NEWSLETTER_DAY", "THU")
    newsletter_hour: int = int(_env("NEWSLETTER_HOUR", "09"))
    newsletter_minute: int = int(_env("NEWSLETTER_MINUTE", "00"))

    @property
    def regions(self) -> list[str]:
        return [r.strip() for r in self.regions_csv.split(",") if r.strip()]


settings = Settings()
