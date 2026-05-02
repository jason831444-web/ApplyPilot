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
    "Microsoft Excel": [r"\bmicrosoft excel\b", r"\bexcel\b"],
}

NON_TECHNICAL_SKILLS = {"English", "Korean"}


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
        r"\bP\s+R\s+O\s+J\s+E\s+C\s+T\s+S\b": "PROJECTS",
        r"\bC\s+A\s+M\s+P\s+U\s+S\s+I\s+N\s+V\s+O\s+L\s+V\s+E\s+M\s+E\s+N\s+T\b": "CAMPUS INVOLVEMENT",
    }
    for pattern, replacement in replacements.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    return "\n".join(line.strip() for line in normalized.splitlines() if line.strip())


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
        clean_line = clean_project_line(line)
        if not clean_line or is_non_project_line(clean_line):
            continue
        if "|" in clean_line:
            clean_line = clean_line.split("|", 1)[0].strip()
        if looks_like_project_title(clean_line):
            projects.append(clean_line[:180])
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
        if 1 <= len(candidate.split()) <= 8 and not is_non_project_line(candidate):
            projects.append(candidate[:180])
    return unique(projects)


def build_experience_summary(text: str, skills: list[str], projects: list[str]) -> str:
    _ = text
    skill_phrase = join_human(skills[:8]) if skills else "software engineering"
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


def canonical_heading(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().upper().replace(" AND ", " & "))


def clean_project_line(line: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"^[\-*\s]+", "", line)).strip()


def looks_like_project_title(line: str) -> bool:
    if len(line.split()) > 14:
        return False
    if re.search(r"\b(built|developed|implemented|designed|created|used|analyzed|integrated)\b", line, re.IGNORECASE):
        return False
    return bool(re.search(r"[A-Za-z]{3,}", line))


def is_non_project_line(line: str) -> bool:
    lower = line.lower()
    blocked = ["email", "github", "linkedin", "coursework", "university", "gpa", "education", "campus"]
    return any(value in lower for value in blocked)


def join_human(values: list[str]) -> str:
    clean_values = [value for value in values if value]
    if len(clean_values) <= 1:
        return "".join(clean_values)
    return ", ".join(clean_values[:-1]) + f", and {clean_values[-1]}"


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.lower().strip()
        if key and key not in seen:
            seen.add(key)
            result.append(value.strip())
    return result
