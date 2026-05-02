import re
from difflib import SequenceMatcher


MAX_EVIDENCE_TEXT_LENGTH = 280


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def make_evidence(kind: str, label: str, text: str, source: str = "job_description") -> dict:
    return {
        "type": kind,
        "label": label,
        "text": clamp_snippet(text),
        "source": source,
    }


def dedupe_evidence(items: list[dict]) -> list[dict]:
    seen: set[tuple[str, str, str, str]] = set()
    kept_by_label: dict[tuple[str, str, str], list[str]] = {}
    deduped: list[dict] = []

    for item in items:
        text = clamp_snippet(str(item.get("text", "")))
        key = (
            str(item.get("type", "")).strip().lower(),
            str(item.get("label", "")).strip().lower(),
            str(item.get("source", "")).strip().lower(),
            normalize_whitespace(text).lower(),
        )
        if key in seen:
            continue
        label_key = key[:3]
        similar_texts = kept_by_label.setdefault(label_key, [])
        if is_similar_to_existing(text, similar_texts):
            continue
        if len(similar_texts) >= 2:
            continue
        seen.add(key)
        similar_texts.append(text)
        item["text"] = text
        deduped.append(item)

    return deduped


def phrase_window(text: str, start: int, end: int, window: int = 90) -> str:
    if not text:
        return ""

    left = sentence_left_boundary(text, start)
    right = sentence_right_boundary(text, end)
    snippet = text[left:right].strip()

    if len(normalize_whitespace(snippet)) > MAX_EVIDENCE_TEXT_LENGTH:
        left = word_left_boundary(text, max(0, start - window))
        right = word_right_boundary(text, min(len(text), end + window))
        snippet = text[left:right].strip()

    return clamp_snippet(snippet)


def sentence_left_boundary(text: str, start: int) -> int:
    boundary = max(text.rfind(".", 0, start), text.rfind("!", 0, start), text.rfind("?", 0, start), text.rfind("\n", 0, start))
    return word_left_boundary(text, boundary + 1 if boundary >= 0 else 0)


def sentence_right_boundary(text: str, end: int) -> int:
    candidates = [position for marker in ".!?\n" if (position := text.find(marker, end)) != -1]
    boundary = min(candidates) + 1 if candidates else len(text)
    return word_right_boundary(text, boundary)


def word_left_boundary(text: str, start: int) -> int:
    start = max(0, min(start, len(text)))
    while start > 0 and not text[start - 1].isspace() and text[start - 1] not in ".!?,;:\n":
        start -= 1
    return start


def word_right_boundary(text: str, end: int) -> int:
    end = max(0, min(end, len(text)))
    while end < len(text) and not text[end].isspace() and text[end] not in ".!?,;:\n":
        end += 1
    return end


def clamp_snippet(text: str, max_length: int = MAX_EVIDENCE_TEXT_LENGTH) -> str:
    snippet = normalize_whitespace(text)
    if len(snippet) <= max_length:
        return snippet

    clipped = snippet[:max_length].rstrip()
    boundary = max(clipped.rfind("."), clipped.rfind("!"), clipped.rfind("?"))
    if boundary >= 80:
        return clipped[: boundary + 1]

    word_boundary = clipped.rfind(" ")
    if word_boundary >= 80:
        return clipped[:word_boundary].rstrip()
    return clipped


def is_similar_to_existing(text: str, existing_texts: list[str]) -> bool:
    normalized = normalize_whitespace(text).lower()
    for existing in existing_texts:
        existing_normalized = normalize_whitespace(existing).lower()
        if normalized in existing_normalized or existing_normalized in normalized:
            return True
        if SequenceMatcher(None, normalized, existing_normalized).ratio() >= 0.88:
            return True
    return False
