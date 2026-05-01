import re


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def make_evidence(kind: str, label: str, text: str, source: str = "job_description") -> dict:
    return {
        "type": kind,
        "label": label,
        "text": normalize_whitespace(text)[:300],
        "source": source,
    }


def dedupe_evidence(items: list[dict]) -> list[dict]:
    seen: set[tuple[str, str, str, str]] = set()
    deduped: list[dict] = []

    for item in items:
        key = (
            str(item.get("type", "")).strip().lower(),
            str(item.get("label", "")).strip().lower(),
            str(item.get("source", "")).strip().lower(),
            normalize_whitespace(str(item.get("text", ""))).lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped


def phrase_window(text: str, start: int, end: int, window: int = 90) -> str:
    left = max(0, start - window)
    right = min(len(text), end + window)
    return normalize_whitespace(text[left:right])
