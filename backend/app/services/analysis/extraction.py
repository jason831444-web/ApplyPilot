import re

from app.services.analysis.evidence import dedupe_evidence, make_evidence, phrase_window
from app.services.analysis.rules import (
    AUTHORIZATION_HIGH_PATTERNS,
    AUTHORIZATION_MEDIUM_PATTERNS,
    AUTHORIZATION_POSITIVE_PATTERNS,
    EXPERIENCE_RULES,
    PREFERRED_SECTION_PATTERNS,
    REQUIRED_SECTION_PATTERNS,
    SKILL_PATTERNS,
)


def unique_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def split_sections(text: str) -> list[tuple[str, str]]:
    inline_sections = split_inline_sections(text)
    if inline_sections:
        return inline_sections

    lines = [line.strip() for line in text.splitlines()]
    sections: list[tuple[str, list[str]]] = [("general", [])]
    heading_pattern = re.compile(r"^[A-Za-z /&+-]{3,70}:?$")

    for line in lines:
        if not line:
            continue
        clean = line.rstrip(":").strip()
        if heading_pattern.match(line) and len(line.split()) <= 6:
            sections.append((clean.lower(), []))
        else:
            sections[-1][1].append(line)

    return [(heading, "\n".join(body)) for heading, body in sections if body]


def split_inline_sections(text: str) -> list[tuple[str, str]]:
    heading_pattern = re.compile(
        r"(?i)\b("
        r"preferred qualifications?|minimum qualifications?|basic qualifications?|"
        r"nice to have|what you need|requirements?|qualifications?|required|preferred|bonus"
        r")\s*:"
    )
    matches = list(heading_pattern.finditer(text))
    if not matches:
        return []

    sections: list[tuple[str, str]] = []
    prefix = text[: matches[0].start()].strip()
    if prefix:
        sections.append(("general", prefix))

    for index, match in enumerate(matches):
        heading = match.group(1).strip().lower()
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        if body:
            sections.append((heading, body))

    return sections


def section_kind(heading: str) -> str:
    if any(re.search(pattern, heading, re.IGNORECASE) for pattern in PREFERRED_SECTION_PATTERNS):
        return "preferred"
    if any(re.search(pattern, heading, re.IGNORECASE) for pattern in REQUIRED_SECTION_PATTERNS):
        return "required"
    return "general"


def find_skills(text: str) -> list[str]:
    found: list[tuple[int, int, str]] = []
    for index, (skill, patterns) in enumerate(SKILL_PATTERNS.items()):
        starts = [
            match.start()
            for pattern in patterns
            for match in re.finditer(pattern, text, re.IGNORECASE)
        ]
        if starts:
            found.append((min(starts), index, skill))
    return [skill for _start, _index, skill in sorted(found)]


def extract_skills_by_requirement(text: str) -> tuple[list[str], list[str], list[dict]]:
    required: list[str] = []
    preferred: list[str] = []
    evidence: list[dict] = []
    has_clean_skill_sections = False

    for heading, body in split_sections(text):
        skills = find_skills(body)
        if not skills:
            continue
        kind = section_kind(heading)
        if kind in {"required", "preferred"}:
            has_clean_skill_sections = True
        if kind == "preferred":
            preferred.extend(skills)
        elif kind == "required":
            required.extend(skills)
        else:
            paragraph_hits = re.split(r"(?<=[.!?])\s+|\n+", body)
            for paragraph in paragraph_hits:
                if re.search(r"\b(require|required|qualification|must have|need|experience with)\b", paragraph, re.IGNORECASE):
                    required.extend(find_skills(paragraph))

        for skill in skills:
            match = first_skill_match(skill, body)
            evidence_text = phrase_window(body, match.start(), match.end()) if match else f"{heading}: {skill}"
            evidence.append(make_evidence("skill", skill, evidence_text))

    if not has_clean_skill_sections:
        required = find_skills(text)
        for skill in required:
            match = first_skill_match(skill, text)
            evidence_text = phrase_window(text, match.start(), match.end()) if match else skill
            evidence.append(make_evidence("skill", skill, evidence_text))

    required = unique_preserve(required)
    preferred = [skill for skill in unique_preserve(preferred) if skill not in required]
    return required, preferred, dedupe_evidence(evidence)


def first_skill_match(skill: str, text: str) -> re.Match[str] | None:
    for pattern in SKILL_PATTERNS.get(skill, []):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match
    return None


def extract_experience_signals(text: str) -> tuple[list[dict], list[dict], list[dict]]:
    all_signals: list[dict] = []
    positive: list[dict] = []
    negative: list[dict] = []

    for rule in EXPERIENCE_RULES:
        for match in re.finditer(rule.pattern, text, re.IGNORECASE):
            item = make_evidence("seniority", rule.label, phrase_window(text, match.start(), match.end()))
            item["polarity"] = rule.polarity
            item["severity"] = rule.severity
            all_signals.append(item)
            if rule.polarity == "positive":
                positive.append(item)
            elif rule.polarity == "negative":
                negative.append(item)

    all_signals = dedupe_evidence(all_signals)
    positive = [signal for signal in all_signals if signal.get("polarity") == "positive"]
    negative = [signal for signal in all_signals if signal.get("polarity") == "negative"]
    return all_signals, positive, negative


def extract_authorization(text: str) -> tuple[str, list[dict]]:
    evidence: list[dict] = []

    for pattern in AUTHORIZATION_HIGH_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            evidence.append(make_evidence("authorization", "high", phrase_window(text, match.start(), match.end())))
    if evidence:
        return "high", evidence

    for pattern in AUTHORIZATION_MEDIUM_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            evidence.append(make_evidence("authorization", "medium", phrase_window(text, match.start(), match.end())))
    if evidence:
        return "medium", evidence

    for pattern in AUTHORIZATION_POSITIVE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            evidence.append(make_evidence("authorization", "low", phrase_window(text, match.start(), match.end())))
    if evidence:
        return "low", evidence

    return "unknown", []


def detect_employment_type(text: str) -> str | None:
    if re.search(r"\bintern(ship)?\b", text, re.IGNORECASE):
        return "internship"
    if re.search(r"\bcontract\b", text, re.IGNORECASE):
        return "contract"
    if re.search(r"\bpart[- ]time\b", text, re.IGNORECASE):
        return "part_time"
    if re.search(r"\bfull[- ]time\b", text, re.IGNORECASE):
        return "full_time"
    return None
