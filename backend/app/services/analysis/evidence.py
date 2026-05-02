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
    _ = window
    matched_phrase = text[start:end]
    return extract_sentence_evidence(text, matched_phrase)


def extract_sentence_evidence(text: str, matched_phrase: str, max_chars: int = MAX_EVIDENCE_TEXT_LENGTH) -> str:
    if not text or not matched_phrase:
        return ""

    units = sentence_like_units(text)
    phrase = normalize_whitespace(matched_phrase).lower()
    for unit in units:
        if phrase in normalize_whitespace(unit).lower():
            return clean_evidence_text(trim_sentence_unit(unit, matched_phrase, max_chars))

    paragraph = paragraph_containing_phrase(text, matched_phrase)
    if paragraph:
        return clean_evidence_text(trim_sentence_unit(paragraph, matched_phrase, max_chars))

    return clean_evidence_text(clamp_snippet(matched_phrase, max_chars))


def sentence_like_units(text: str) -> list[str]:
    normalized_lines = [normalize_whitespace(line) for line in text.replace("\r", "\n").split("\n")]
    units: list[str] = []
    heading_pattern = re.compile(r"^[A-Z][A-Za-z /&+-]{2,70}:?$")

    for line in normalized_lines:
        if not line:
            continue
        if heading_pattern.match(line) and len(line.split()) <= 6:
            continue
        sentence_parts = re.split(r"(?<=[.!?])\s+", line)
        for part in sentence_parts:
            clean_part = strip_heading_prefix(part)
            if clean_part:
                units.append(clean_part)
    return units


def paragraph_containing_phrase(text: str, matched_phrase: str) -> str:
    phrase = normalize_whitespace(matched_phrase).lower()
    for paragraph in re.split(r"\n\s*\n|\n", text):
        normalized = normalize_whitespace(strip_heading_prefix(paragraph))
        if phrase in normalized.lower():
            return normalized
    return ""


def strip_heading_prefix(value: str) -> str:
    text = normalize_whitespace(value)
    return re.sub(
        r"^(?:About The Role|Who Should Not Apply|Who Should Apply|Responsibilities|Qualifications|Requirements|Preferred Qualifications)\s*:?\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )


def trim_sentence_unit(unit: str, matched_phrase: str, max_chars: int) -> str:
    sentence = normalize_whitespace(unit)
    if len(sentence) <= max_chars:
        return sentence

    match_index = sentence.lower().find(normalize_whitespace(matched_phrase).lower())
    if match_index < 0:
        return clamp_snippet(sentence, max_chars)

    if match_index <= max_chars // 2:
        return clamp_snippet(sentence, max_chars)

    clause_start = nearest_clause_start(sentence, match_index, max_chars)
    excerpt = sentence[clause_start:]
    if clause_start > 0:
        excerpt = f"...{excerpt}"
    return clamp_snippet(excerpt, max_chars)


def nearest_clause_start(sentence: str, match_index: int, max_chars: int) -> int:
    search_start = max(0, match_index - max_chars // 2)
    candidates = [
        sentence.rfind(marker, search_start, match_index)
        for marker in [". ", "! ", "? ", "; ", ": ", ", "]
    ]
    boundary = max(candidates)
    if boundary >= search_start:
        return word_left_boundary(sentence, boundary + 2)
    return word_left_boundary(sentence, search_start)


def clean_evidence_text(text: str) -> str:
    cleaned = normalize_whitespace(text)
    cleaned = re.sub(r"^[\s\-–—:;,.!?()\[\]{}]+", "", cleaned)
    cleaned = remove_broken_leading_fragment(cleaned)
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def remove_broken_leading_fragment(text: str) -> str:
    period_index = text.find(".")
    if 0 <= period_index <= 35:
        leading_words = text[:period_index].split()
        remainder = text[period_index + 1 :].strip()
        if len(leading_words) < 3 and remainder:
            return remainder
    return text


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

    ellipsis_prefix = snippet.startswith("...")
    available_length = max_length - 3 if ellipsis_prefix else max_length
    body = snippet[3:] if ellipsis_prefix else snippet
    clipped = body[:available_length].rstrip()
    boundary = max(clipped.rfind("."), clipped.rfind("!"), clipped.rfind("?"))
    if boundary >= 80:
        result = clipped[: boundary + 1]
        return f"...{result}" if ellipsis_prefix else result

    word_boundary = clipped.rfind(" ")
    if word_boundary >= 80:
        result = clipped[:word_boundary].rstrip()
        return f"...{result}..." if ellipsis_prefix else f"{result}..."
    return f"...{clipped}..." if ellipsis_prefix else f"{clipped}..."


def is_similar_to_existing(text: str, existing_texts: list[str]) -> bool:
    normalized = normalize_whitespace(text).lower()
    for existing in existing_texts:
        existing_normalized = normalize_whitespace(existing).lower()
        if normalized in existing_normalized or existing_normalized in normalized:
            return True
        if SequenceMatcher(None, normalized, existing_normalized).ratio() >= 0.88:
            return True
    return False
