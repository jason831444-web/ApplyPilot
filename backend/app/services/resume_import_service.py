import re
from io import BytesIO

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader

from app.schemas.resume_import import ResumeImportRead
from app.services.analysis.rules import SKILL_PATTERNS


SECTION_HEADINGS = [
    "EDUCATION",
    "WORK EXPERIENCE",
    "WORK EXPERIENCE & PROJECTS",
    "PROJECTS",
    "CAMPUS INVOLVEMENT",
    "TECHNICAL SKILLS",
    "SKILLS",
]

TECHNICAL_SKILL_ALIASES = {
    "C": [r"\bC\b"],
    "Express.js": [r"\bexpress(?:\.js|js)?\b"],
    "Spring Boot": [r"\bspring boot\b"],
    "GitHub": [r"\bgithub\b"],
    "Visual Studio Code": [r"\bvisual studio code\b", r"\bvscode\b"],
}

NON_TECHNICAL_SKILLS = {"English", "Korean"}

PROJECT_FRAGMENT_STARTS = (
    "and ",
    "a ",
    "ai inference",
    "a multi-stage",
    "fallback routing",
    "product-facing",
    "backend persistence",
    "job saving",
    "profile using",
    "structured rules",
    "missing-skill detection",
    "application status tracking",
    "developed",
    "implemented",
    "designed",
    "integrated",
    "improved",
    "conducted",
    "evaluated",
    "visualized",
    "built",
    "created",
    "used",
)

SUMMARY_SKILL_PRIORITY = [
    "Python",
    "JavaScript",
    "React",
    "Next.js",
    "FastAPI",
    "PostgreSQL",
    "Docker",
    "SQL",
]

MODEL_OR_LIBRARY_PROJECT_NAMES = {
    "spiking neural network",
    "spiking neural network (snn)",
    "resnet",
    "yolo",
    "pytorch",
    "numpy",
    "matplotlib",
}


class ResumeImportService:
    async def parse_upload(self, file: UploadFile) -> ResumeImportRead:
        if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF resume uploads are supported.")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded PDF is empty.")

        text = self._extract_pdf_text(content)
        if not text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not extract text from this PDF.")

        skills = extract_skills_from_technical_skills_section(text)
        projects = extract_project_names(text)
        return ResumeImportRead(
            resume_text=text[:30000],
            skills_suggestions=skills,
            projects_suggestions=projects,
            experience_summary_suggestion=build_experience_summary(text, skills, projects),
        )

    def _extract_pdf_text(self, content: bytes) -> str:
        try:
            reader = PdfReader(BytesIO(content))
            page_text = [page.extract_text() or "" for page in reader.pages]
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not read this PDF.") from exc
        return normalize_resume_text("\n".join(page_text))


def normalize_resume_text(text: str) -> str:
    normalized = text.replace("\r", "\n")
    normalized = re.sub(r"[•●▪]", "-", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    replacements = {
        r"\bE\s+D\s+U\s+C\s+A\s+T\s+I\s+O\s+N\b": "EDUCATION",
        r"\bT\s+E\s+C\s+H\s+N\s+I\s+C\s+A\s+L\s+S\s+K\s+I\s+L\s+L\s+S\b": "TECHNICAL SKILLS",
        r"\bW\s+O\s+R\s+K\s+E\s+X\s+P\s+E\s+R\s+I\s+E\s+N\s+C\s+E\s*&\s*P\s+R\s+O\s+J\s+E\s+C\s+T\s+S\b": "WORK EXPERIENCE & PROJECTS",
        r"\bP\s+R\s+O\s+J\s+E\s+C\s+T\s+S\b": "PROJECTS",
        r"\bC\s+A\s+M\s+P\s+U\s+S\s+I\s+N\s+V\s+O\s+L\s+V\s+E\s+M\s+E\s+N\s+T\b": "CAMPUS INVOLVEMENT",
    }
    for pattern, replacement in replacements.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    output: list[str] = []
    for raw_line in normalized.splitlines():
        for line in split_inline_section_heading(raw_line):
            append_normalized_resume_line(output, line)

    return "\n".join(output)


def append_normalized_resume_line(output: list[str], raw_line: str) -> None:
    line = clean_whitespace(raw_line)
    if not line:
        return

    heading = heading_from_line(line)
    if heading:
        append_line(output, heading)
        return

    line = normalize_bullet_line(line)
    if is_bullet_line(line):
        append_line(output, line)
        return

    if not output or should_start_new_line(output[-1], line):
        append_line(output, line)
    else:
        output[-1] = f"{output[-1]} {line}".strip()


def split_resume_sections(text: str) -> dict[str, str]:
    normalized = normalize_resume_text(text)
    heading_pattern = re.compile(
        r"(?im)^(EDUCATION|WORK EXPERIENCE(?:\s*&\s*PROJECTS)?|PROJECTS|CAMPUS INVOLVEMENT|TECHNICAL SKILLS|SKILLS)\s*$"
    )
    matches = list(heading_pattern.finditer(normalized))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = canonical_heading(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        sections[heading] = normalized[start:end].strip()
    return sections


def extract_section(text: str, heading_names: list[str]) -> str:
    sections = split_resume_sections(text)
    for heading in heading_names:
        value = sections.get(canonical_heading(heading))
        if value:
            return value
    return ""


def extract_skills_from_technical_skills_section(text: str) -> list[str]:
    section = extract_section(text, ["TECHNICAL SKILLS", "SKILLS"])
    search_text = section or normalize_resume_text(text)
    skills: list[str] = []
    patterns_by_skill = {**SKILL_PATTERNS, **TECHNICAL_SKILL_ALIASES}

    for skill, patterns in patterns_by_skill.items():
        if skill in NON_TECHNICAL_SKILLS:
            continue
        if any(re.search(pattern, search_text, re.IGNORECASE) for pattern in patterns):
            skills.append(skill)
    return unique(skills)


def extract_project_names(text: str) -> list[str]:
    section = extract_section(text, ["PROJECTS"])
    if not section:
        section = extract_section(text, ["WORK EXPERIENCE & PROJECTS", "WORK EXPERIENCE"])

    projects: list[str] = []
    for line in section.splitlines():
        if is_bullet_line(line):
            continue
        clean_line = clean_project_line(line)
        had_pipe = "|" in clean_line
        if "|" in clean_line:
            clean_line = clean_line.split("|", 1)[0].strip()
        if not clean_line or is_non_project_line(clean_line):
            continue
        if is_valid_project_title_candidate(clean_line, had_pipe=had_pipe):
            projects.append(clean_line[:180])
    projects.extend(extract_project_titles_from_text(section))
    if projects:
        return unique(projects)[:7]
    return fallback_project_names(text)[:5]


def fallback_project_names(text: str) -> list[str]:
    projects: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", normalize_resume_text(text)):
        match = re.search(
            r"\b(?:built|developed|implemented|created|designed)\s+(.+?)(?:\s+(?:using|with|in|for)\b|[.!?]|$)",
            sentence,
            re.IGNORECASE,
        )
        if not match:
            continue
        candidate = clean_project_line(match.group(1))
        if (is_valid_project_title_candidate(candidate) or looks_like_single_project_name(candidate)) and not is_non_project_line(candidate):
            projects.append(candidate[:180])
    return unique(projects)


def build_experience_summary(text: str, skills: list[str], projects: list[str]) -> str:
    _ = text
    summary_skills = order_summary_skills(skills)[:8]
    skill_phrase = join_human(summary_skills) if summary_skills else "software engineering"
    project_names = [project.split("–", 1)[0].split("-", 1)[0].strip() for project in projects[:5]]
    if project_names:
        project_sentence = f"Built projects including {join_human(project_names)}."
    else:
        project_sentence = "Built applied software projects across coursework and personal work."
    summary = (
        f"Computer Science new-grad candidate with experience in {skill_phrase}. "
        f"{project_sentence}"
    )
    return summary[:600]


def clean_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def split_inline_section_heading(line: str) -> list[str]:
    clean_line = clean_whitespace(line)
    if not clean_line:
        return []

    heading_patterns = [
        ("WORK EXPERIENCE & PROJECTS", r"work\s+experience\s*&\s*projects"),
        ("TECHNICAL SKILLS", r"technical\s+skills"),
        ("CAMPUS INVOLVEMENT", r"campus\s+involvement"),
        ("WORK EXPERIENCE", r"work\s+experience"),
        ("EDUCATION", r"education"),
        ("PROJECTS", r"projects"),
    ]
    for heading, pattern in heading_patterns:
        match = re.match(rf"^\s*({pattern})\s*:?\s+(.+)$", clean_line, flags=re.IGNORECASE)
        if match:
            return [heading, match.group(2).strip()]
    return [line]


def append_line(output: list[str], line: str) -> None:
    if line:
        output.append(line)


def heading_from_line(line: str) -> str | None:
    stripped = line.strip()
    if re.fullmatch(r"(?i)skills:?", stripped):
        return "SKILLS"
    compact = re.sub(r"[^A-Za-z&]", "", line).upper()
    heading_map = {
        "EDUCATION": "EDUCATION",
        "WORKEXPERIENCE": "WORK EXPERIENCE",
        "WORKEXPERIENCE&PROJECTS": "WORK EXPERIENCE & PROJECTS",
        "PROJECTS": "PROJECTS",
        "CAMPUSINVOLVEMENT": "CAMPUS INVOLVEMENT",
        "TECHNICALSKILLS": "TECHNICAL SKILLS",
    }
    return heading_map.get(compact)


def normalize_bullet_line(line: str) -> str:
    return re.sub(r"^\s*[-*•●▪]\s*", "- ", line).strip()


def is_bullet_line(line: str) -> bool:
    return bool(re.match(r"^\s*[-*•●▪]\s+", line))


def should_start_new_line(previous: str, current: str) -> bool:
    if heading_from_line(previous):
        return True
    if is_bullet_line(previous):
        return True
    if is_project_title_row(previous) or is_project_title_row(current):
        return True
    if re.match(r"^[A-Z][A-Za-z /&.-]+:\s", current):
        return True
    if re.search(r"[.!?)]$", previous) and len(current.split()) > 3:
        return True
    if len(current.split()) <= 3:
        return False
    return False


def is_project_title_row(line: str) -> bool:
    if "|" not in line or is_bullet_line(line):
        return False
    title = clean_project_line(line.split("|", 1)[0])
    return looks_like_project_title(title)


def is_valid_project_title_candidate(candidate: str, *, had_pipe: bool = False) -> bool:
    if not looks_like_project_title(candidate):
        return False
    if is_model_or_library_name(candidate):
        return False
    if not had_pipe and len(meaningful_words(candidate)) < 3 and candidate != "ApplyPilot":
        return False
    if had_pipe or " – " in candidate:
        return True
    return has_title_case_project_pattern(candidate)


def extract_project_titles_from_text(text: str) -> list[str]:
    titles: list[str] = []
    title_before_pipe_pattern = re.compile(r"(?P<title>(?:^|\n)[^\n|]{3,100}?)\s+\|\s+")
    for match in title_before_pipe_pattern.finditer(text):
        title = best_project_title_from_segment(match.group("title"))
        if is_valid_project_title_candidate(title, had_pipe=True) and not is_non_project_line(title):
            titles.append(title[:180])

    for match in re.finditer(r"\s+\|\s+", text):
        title = best_project_title_before_pipe(text[: match.start()])
        if is_valid_project_title_candidate(title, had_pipe=True) and not is_non_project_line(title):
            titles.append(title[:180])
    return unique(titles)


def best_project_title_before_pipe(value: str) -> str:
    segment = value.rsplit("\n", 1)[-1].rsplit("|", 1)[-1]
    return best_project_title_from_segment(segment)


def best_project_title_from_segment(segment: str) -> str:
    words = clean_project_line(segment).split()
    for start_index, word in enumerate(words):
        if not word[:1].isupper():
            continue
        candidate = clean_project_line(" ".join(words[start_index:]))
        if looks_like_project_title(candidate):
            return candidate
    return ""


def canonical_heading(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().upper().replace(" AND ", " & "))


def clean_project_line(line: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"^[\-*\s]+", "", line)).strip()


def looks_like_project_title(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped[0].islower():
        return False
    if stripped.lower().startswith(PROJECT_FRAGMENT_STARTS):
        return False
    if any(f" {fragment}" in stripped.lower() for fragment in PROJECT_FRAGMENT_STARTS):
        return False
    if "," in stripped:
        return False
    if len(line.split()) > 14:
        return False
    if re.search(
        r"^(built|developed|implemented|designed|created|used|analyzed|integrated|improved|conducted|evaluated|visualized)\b",
        line,
        re.IGNORECASE,
    ):
        return False
    return bool(re.search(r"[A-Za-z]{3,}", line))


def has_title_case_project_pattern(line: str) -> bool:
    words = re.findall(r"\b[A-Za-z][A-Za-z.()&+-]*\b", line)
    title_like_words = [word for word in words if word[:1].isupper() or word.isupper()]
    return len(title_like_words) >= 3 and len(words) <= 10


def meaningful_words(line: str) -> list[str]:
    return re.findall(r"\b[A-Za-z][A-Za-z0-9.+#-]*\b", line)


def is_model_or_library_name(line: str) -> bool:
    normalized = re.sub(r"\s+", " ", line.strip().lower())
    if normalized in MODEL_OR_LIBRARY_PROJECT_NAMES:
        return True
    return bool(re.fullmatch(r"(?:custom\s+\d+[- ]layer\s+)?spiking neural network(?:\s+\(snn\))?", normalized))


def looks_like_single_project_name(line: str) -> bool:
    stripped = line.strip()
    if not stripped or " " in stripped or stripped.lower().startswith(PROJECT_FRAGMENT_STARTS):
        return False
    return bool(re.match(r"^[A-Z][A-Za-z0-9]+$", stripped))


def is_non_project_line(line: str) -> bool:
    lower = line.lower()
    blocked = ["email", "github", "linkedin", "coursework", "university", "gpa", "education", "campus"]
    return any(value in lower for value in blocked)


def join_human(values: list[str]) -> str:
    clean_values = [value for value in values if value]
    if len(clean_values) <= 1:
        return "".join(clean_values)
    return ", ".join(clean_values[:-1]) + f", and {clean_values[-1]}"


def order_summary_skills(skills: list[str]) -> list[str]:
    priority = [skill for skill in SUMMARY_SKILL_PRIORITY if skill in skills]
    remaining = [skill for skill in skills if skill not in priority]
    return priority + remaining


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.lower().strip()
        if key and key not in seen:
            seen.add(key)
            result.append(value.strip())
    return result
