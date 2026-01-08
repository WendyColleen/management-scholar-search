from __future__ import annotations

from typing import Optional

from .config import settings


def summarize_with_openai(title: str, text: str) -> Optional[str]:
    """Return a 1-2 sentence summary, or None if no key / error."""
    if not settings.openai_api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        prompt = (
            "Summarize the following item in 1-2 sentences for management scholars. "
            "Focus on who it's for, what it is, and deadlines if present.\n\n"
            f"TITLE: {title}\n\nCONTENT: {text}"
        )
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        # openai python returns output_text convenience
        out = getattr(resp, "output_text", None)
        if out:
            return out.strip()

        # fallback parse
        if hasattr(resp, "output") and resp.output:
            # join text parts
            parts = []
            for o in resp.output:
                for c in getattr(o, "content", []) or []:
                    if getattr(c, "type", "") == "output_text":
                        parts.append(getattr(c, "text", ""))
            joined = "\n".join(parts).strip()
            return joined or None
    except Exception:
        return None

    return None
