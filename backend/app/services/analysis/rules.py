from dataclasses import dataclass
import re


SKILL_PATTERNS: dict[str, list[str]] = {
    "Python": [r"\bpython\b"],
    "Java": [r"\bjava\b"],
    "JavaScript": [r"\bjavascript\b", r"(?<!\.)\bjs\b"],
    "TypeScript": [r"\btypescript\b", r"(?<!\.)\bts\b"],
    "React": [r"\breact(?:\.js)?\b"],
    "Next.js": [r"\bnext(?:\.js|js)?\b"],
    "Node.js": [r"\bnode(?:\.js|js)?\b"],
    "FastAPI": [r"\bfastapi\b"],
    "Django": [r"\bdjango\b"],
    "Flask": [r"\bflask\b"],
    "SQL": [r"\bsql\b"],
    "PostgreSQL": [r"\bpostgresql\b", r"\bpostgres\b"],
    "MySQL": [r"\bmysql\b"],
    "MongoDB": [r"\bmongodb\b", r"\bmongo\b"],
    "Redis": [r"\bredis\b"],
    "Docker": [r"\bdocker\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "AWS": [r"\baws\b", r"\bamazon web services\b"],
    "Azure": [r"\bazure\b"],
    "GCP": [r"\bgcp\b", r"\bgoogle cloud\b"],
    "Git": [r"\bgit\b", r"\bgithub\b", r"\bgitlab\b"],
    "CI/CD": [r"\bci/cd\b", r"\bcontinuous integration\b", r"\bcontinuous delivery\b"],
    "REST API": [r"\brest(?:ful)? api(?:s)?\b", r"\brest\b"],
    "GraphQL": [r"\bgraphql\b"],
    "Linux": [r"\blinux\b", r"\bunix\b"],
    "TensorFlow": [r"\btensorflow\b"],
    "PyTorch": [r"\bpytorch\b"],
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b"],
    "Computer Vision": [r"\bcomputer vision\b"],
    "HTML": [r"\bhtml\b"],
    "CSS": [r"\bcss\b"],
    "Tailwind CSS": [r"\btailwind(?: css)?\b"],
}

REQUIRED_SECTION_PATTERNS = [
    r"requirements?",
    r"qualifications?",
    r"required",
    r"what you need",
    r"minimum qualifications?",
    r"basic qualifications?",
]

PREFERRED_SECTION_PATTERNS = [
    r"preferred",
    r"nice to have",
    r"bonus",
    r"preferred qualifications?",
    r"plus",
]


@dataclass(frozen=True)
class SignalRule:
    label: str
    pattern: str
    polarity: str
    severity: int = 1


EXPERIENCE_RULES = [
    SignalRule("new grad", r"\bnew grad(?:uate)?s?\b", "positive", 3),
    SignalRule("entry-level", r"\bentry[- ]level\b", "positive", 3),
    SignalRule("junior", r"\bjunior\b", "positive", 2),
    SignalRule("university graduate", r"\buniversity graduate\b|\bcollege graduate\b|\brecent graduate\b", "positive", 3),
    SignalRule("internship", r"\binternship\b|\bintern\b", "positive", 1),
    SignalRule("0-1 years", r"\b0\s*(?:-|–|\bto\b)\s*1\s+years?\b", "positive", 3),
    SignalRule("0-2 years", r"\b0\s*(?:-|–|\bto\b)\s*2\s+years?\b", "positive", 3),
    SignalRule("1+ years", r"\b1\s*\+\s+years?\b|\bat least 1 year\b|\bminimum 1 year\b|\b1 or more years?\b", "positive", 2),
    SignalRule("2+ years", r"\b2\s*\+\s+years?\b|\bat least 2 years\b|\bminimum 2 years\b|\b2 or more years?\b", "mixed", 1),
    SignalRule("3+ years", r"\b3\s*\+\s+years?\b|\bat least 3 years\b|\bminimum 3 years\b|\b3 or more years?\b", "negative", 2),
    SignalRule("5+ years", r"\b5\s*\+\s+years?\b|\bat least 5 years\b|\bminimum 5 years\b|\b5 or more years?\b", "negative", 3),
    SignalRule("senior", r"\bsenior\b|\bsr\.\b", "negative", 3),
    SignalRule("staff", r"\bstaff\b", "negative", 3),
    SignalRule("principal", r"\bprincipal\b", "negative", 3),
    SignalRule("lead", r"\blead\b", "negative", 3),
    SignalRule("architect", r"\barchitect\b", "negative", 3),
]

AUTHORIZATION_POSITIVE_PATTERNS = [
    r"\bsponsor(?:s|ship)?\b.{0,40}\b(h-?1b|visa|opt|cpt)\b",
    r"\b(h-?1b|visa|opt|cpt)\b.{0,40}\bsponsor",
    r"\bvisa sponsorship is available\b",
]

AUTHORIZATION_HIGH_PATTERNS = [
    r"\bwithout (?:current or future )?sponsorship\b",
    r"\bunable to sponsor\b",
    r"\bno sponsorship\b",
    r"\bdo not sponsor\b",
    r"\bwill not sponsor\b",
    r"\bmust be authorized to work\b.{0,80}\bwithout\b.{0,40}\bsponsorship\b",
    r"\bwithout the need for sponsorship\b",
    r"\brequire(?:s|d)? work authorization\b.{0,80}\bwithout\b.{0,40}\bsponsorship\b",
]

AUTHORIZATION_MEDIUM_PATTERNS = [
    r"\bu\.?s\.? citizenship required\b",
    r"\bus citizenship required\b",
    r"\bsecurity clearance\b",
    r"\bclearance required\b",
]

USER_SPONSORSHIP_NEED_PATTERNS = [
    r"\bf-?1\b",
    r"\bopt\b",
    r"\bcpt\b",
    r"\bh-?1b\b",
    r"\bvisa\b",
    r"\bsponsor",
    r"\bfuture sponsorship\b",
]


def compile_any(patterns: list[str]) -> re.Pattern[str]:
    return re.compile("|".join(f"(?:{pattern})" for pattern in patterns), re.IGNORECASE)
