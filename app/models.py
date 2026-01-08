from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Index


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    title: str
    url: str
    source: str

    published: Optional[datetime] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    item_type: str = "other"  # funding|cfp|conference|journal|other
    region: str = "Global"
    topic: str = "General"

    summary: str = ""
    fingerprint: str = Field(index=True)


Index("idx_item_fingerprint", Item.fingerprint, unique=True)
Index("idx_item_region_type", Item.region, Item.item_type)
