from __future__ import annotations

import re
from dataclasses import dataclass

REGION_KEYWORDS = {
    "North America": [r"\busa\b", r"\bunited states\b", r"\bcanada\b", r"\bmexico\b"],
    "Europe": [r"\beu\b", r"\beurope\b", r"\bhorizon europe\b", r"\berasmus\b", r"\baustria\b", r"\bgermany\b", r"\buk\b", r"\bunited kingdom\b"],
    "Asia": [r"\basia\b", r"\bchina\b", r"\bindia\b", r"\bjapan\b", r"\bkorea\b", r"\bsingapore\b"],
}

TYPE_KEYWORDS = {
    "funding": [r"grant", r"funding", r"call for proposals", r"fellowship", r"tender", r"budget"],
    "cfp": [r"call for papers", r"special issue", r"submit", r"deadline"],
    "conference": [r"conference", r"annual meeting", r"symposium", r"workshop", r"pdw"],
    "journal": [r"journal", r"in-press", r"issue", r"table of contents", r"eTOC"],
}

TOPIC_KEYWORDS = {
    "International Business": [r"international business", r"aib"],
    "Management": [r"management", r"organization", r"leadership"],
    "HR": [r"human resource", r"hr\b", r"talent", r"recruit"],
    "Sustainability": [r"sustainab", r"csr\b", r"esg\b", r"responsible"],
    "Innovation/Tech": [r"innovation", r"ai\b", r"digital", r"technology"],
}


@dataclass
class Tags:
    region: str
    item_type: str
    topic: str


def infer_tags(title: str, summary: str, fallback_region: str = "Global", fallback_type: str = "other") -> Tags:
    text = f"{title}\n{summary}".lower()

    # type
    item_type = fallback_type
    for t, kws in TYPE_KEYWORDS.items():
        if any(re.search(k, text) for k in kws):
            item_type = t
            break

    # region
    region = fallback_region
    for r, kws in REGION_KEYWORDS.items():
        if any(re.search(k, text) for k in kws):
            region = r
            break

    # topic
    topic = "General"
    for tp, kws in TOPIC_KEYWORDS.items():
        if any(re.search(k, text) for k in kws):
            topic = tp
            break

    return Tags(region=region, item_type=item_type, topic=topic)
