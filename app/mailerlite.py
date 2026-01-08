from __future__ import annotations

import requests

from .config import settings

BASE = "https://connect.mailerlite.com/api"


def _headers() -> dict:
    if not settings.email_api_key:
        raise RuntimeError("EMAIL_API_KEY is not set")
    return {
        "Authorization": f"Bearer {settings.email_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def list_groups() -> list[dict]:
    r = requests.get(f"{BASE}/groups", headers=_headers(), timeout=20)
    r.raise_for_status()
    return r.json().get("data", [])


def get_or_create_group(name: str) -> str:
    for g in list_groups():
        if (g.get("name") or "").strip().lower() == name.strip().lower():
            return g["id"]

    r = requests.post(f"{BASE}/groups", json={"name": name}, headers=_headers(), timeout=20)
    r.raise_for_status()
    return r.json()["data"]["id"]


def upsert_subscriber(email: str, group_ids: list[str], fields: dict | None = None) -> dict:
    payload = {
        "email": email,
        "groups": group_ids,
    }
    if fields:
        payload["fields"] = fields

    r = requests.post(f"{BASE}/subscribers", json=payload, headers=_headers(), timeout=20)
    r.raise_for_status()
    return r.json()
