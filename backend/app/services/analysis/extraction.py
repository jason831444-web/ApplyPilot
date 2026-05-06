import re

from app.services.analysis.evidence import dedupe_evidence, make_evidence, phrase_window
from app.services.analysis.rules import (
    AUTHORIZATION_HIGH_PATTERNS,
    AUTHORIZATION_MEDIUM_PATTERNS,
    AUTHORIZATION_POSITIVE_PATTERNS,
    BENEFITS_SECTION_PATTERNS,
    DOMAIN_SIGNAL_LABELS,
    EXPERIENCE_RULES,
    INTERVIEW_SECTION_PATTERNS,
    LEGAL_SECTION_PATTERNS,
    PREFERRED_SECTION_PATTERNS,
    REQUIRED_SECTION_PATTERNS,
    ROLE_SECTION_PATTERNS,
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
        r"about the role|what you'll do|what you will do|responsibilities|our stack|tools for the job|tech stack|"
        r"preferred qualifications?|minimum qualifications?|basic qualifications?|"
        r"nice to have|what you need|requirements?|qualifications?|required|preferred|bonus|"
        r"benefits?|what we offer|compensation|perks?|equal opportunity|eeo|legal|"
        r"interview process|hiring process|recruiting process"
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
    if any(re.search(pattern, heading, re.IGNORECASE) for pattern in BENEFITS_SECTION_PATTERNS):
        return "excluded"
    if any(re.search(pattern, heading, re.IGNORECASE) for pattern in LEGAL_SECTION_PATTERNS):
        return "excluded"
    if any(re.search(pattern, heading, re.IGNORECASE) for pattern in INTERVIEW_SECTION_PATTERNS):
        return "excluded"
    if any(re.search(pattern, heading, re.IGNORECASE) for pattern in PREFERRED_SECTION_PATTERNS):
        return "preferred"
    if any(re.search(pattern, heading, re.IGNORECASE) for pattern in REQUIRED_SECTION_PATTERNS):
        return "required"
    if any(re.search(pattern, heading, re.IGNORECASE) for pattern in ROLE_SECTION_PATTERNS):
        return "role"
    return "general"


def find_skills(text: str, *, include_domain_signals: bool = True) -> list[str]:
    found: list[tuple[int, int, str]] = []
    for index, (skill, patterns) in enumerate(SKILL_PATTERNS.items()):
        if not include_domain_signals and skill in DOMAIN_SIGNAL_LABELS:
            continue
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
    relevant_sections: list[str] = []

    for heading, body in split_sections(text):
        kind = section_kind(heading)
        include_domains = kind != "excluded"
        skills = find_skills(body, include_domain_signals=include_domains)
        if include_domains:
            relevant_sections.append(body)
        if not skills:
            continue
        technical_skills = [skill for skill in skills if skill not in DOMAIN_SIGNAL_LABELS]
        if kind in {"required", "preferred"}:
            has_clean_skill_sections = True
        if kind == "preferred":
            preferred.extend(technical_skills)
        elif kind == "required":
            required.extend(technical_skills)
        elif kind in {"general", "role"}:
            paragraph_hits = re.split(r"(?<=[.!?])\s+|\n+", body)
            for paragraph in paragraph_hits:
                if re.search(r"\b(require|required|qualification|must have|need|experience with)\b", paragraph, re.IGNORECASE):
                    required.extend(skill for skill in find_skills(paragraph) if skill not in DOMAIN_SIGNAL_LABELS)

        for skill in skills:
            match = first_skill_match(skill, body)
            evidence_text = phrase_window(body, match.start(), match.end()) if match else f"{heading}: {skill}"
            evidence.append(make_evidence(evidence_type_for_skill(skill), skill, evidence_text))

    if not has_clean_skill_sections:
        relevant_text = "\n".join(relevant_sections) if relevant_sections else text
        technical_skills = find_skills(text, include_domain_signals=False)
        domain_signals = find_skills(relevant_text, include_domain_signals=True)
        all_skills = unique_preserve(technical_skills + [skill for skill in domain_signals if skill in DOMAIN_SIGNAL_LABELS])
        required = [skill for skill in all_skills if skill not in DOMAIN_SIGNAL_LABELS]
        for skill in all_skills:
            source_text = relevant_text if skill in DOMAIN_SIGNAL_LABELS else text
            match = first_skill_match(skill, source_text)
            evidence_text = phrase_window(source_text, match.start(), match.end()) if match else skill
            evidence.append(make_evidence(evidence_type_for_skill(skill), skill, evidence_text))

    required = unique_preserve(required)
    preferred = [skill for skill in unique_preserve(preferred) if skill not in required]
    return required, preferred, dedupe_evidence(evidence)


def extract_alternative_skill_groups(text: str) -> list[list[str]]:
    groups: list[list[str]] = []
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    choice_pattern = re.compile(
        r"\b(?:at least one of|one of the following|one of|proficiency in at least one of|"
        r"experience with|experience in)\b",
        re.IGNORECASE,
    )

    for sentence in sentences:
        if not sentence.strip():
            continue
        has_choice_language = bool(choice_pattern.search(sentence)) and re.search(r"\bor\b|,", sentence, re.IGNORECASE)
        has_inline_or = bool(re.search(r"\b[A-Za-z+#.]+\s+or\s+[A-Za-z+#.]+\b", sentence))
        if not has_choice_language and not has_inline_or:
            continue
        skills = [skill for skill in find_skills(sentence, include_domain_signals=False) if skill not in DOMAIN_SIGNAL_LABELS]
        if len(skills) >= 2:
            groups.append(unique_preserve(skills))

    return unique_skill_groups(groups)


def unique_skill_groups(groups: list[list[str]]) -> list[list[str]]:
    seen: set[tuple[str, ...]] = set()
    result: list[list[str]] = []
    for group in groups:
        key = tuple(sorted(skill.lower() for skill in group))
        if key not in seen:
            seen.add(key)
            result.append(group)
    return result


def evidence_type_for_skill(skill: str) -> str:
    return "domain" if skill in DOMAIN_SIGNAL_LABELS else "skill"


def first_skill_match(skill: str, text: str) -> re.Match[str] | None:
    for pattern in SKILL_PATTERNS.get(skill, []):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match
    return None


def extract_experience_signals(text: str) -> tuple[list[dict], list[dict], list[dict]]:
    text = suppress_senior_collaboration_context(text)
    all_signals: list[dict] = []
    positive: list[dict] = []
    negative: list[dict] = []

    for rule in EXPERIENCE_RULES:
        for match in re.finditer(rule.pattern, text, re.IGNORECASE):
            if should_skip_experience_signal(rule.label, text, match):
                continue
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


def suppress_senior_collaboration_context(text: str) -> str:
    patterns = [
        r"\bcollaborat(?:e|ing)\s+with\s+senior\s+(?:developers|engineers|team members)(?:\s+and\s+other\s+team members)?",
        r"\bwork(?:ing)?\s+with\s+senior\s+(?:developers|engineers|team members)(?:\s+and\s+other\s+team members)?",
        r"\bsenior\s+(?:developers|engineers)\s+and\s+other\s+team members",
        r"\bsenior\s+team members",
        r"\blearn\s+from\s+senior\s+(?:developers|engineers)",
    ]
    sanitized = text
    for pattern in patterns:
        sanitized = re.sub(pattern, "collaborate with team members", sanitized, flags=re.IGNORECASE)
    return sanitized


def should_skip_experience_signal(label: str, text: str, match: re.Match[str]) -> bool:
    window_start = max(0, match.start() - 80)
    window_end = min(len(text), match.end() + 80)
    context = text[window_start:window_end].lower()

    if label in {"senior", "senior team"}:
        collaboration_patterns = [
            r"collaborat(?:e|ing)\s+with\s+senior\s+(?:developers|engineers|team members)(?:\s+and\s+other\s+team members)?",
            r"work(?:ing)?\s+with\s+senior\s+(?:developers|engineers|team members)(?:\s+and\s+other\s+team members)?",
            r"learn\s+from\s+senior\s+(?:developers|engineers)",
            r"senior\s+team members",
        ]
        return any(re.search(pattern, context) for pattern in collaboration_patterns)

    if label == "junior":
        return bool(re.search(r"\bmentor\s+junior\s+(?:teammates|developers|engineers)\b", context))

    if label == "lead":
        return match.group(0).lower().startswith("leading ")

    return False


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
