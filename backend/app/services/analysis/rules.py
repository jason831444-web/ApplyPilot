from dataclasses import dataclass
import re


SKILL_PATTERNS: dict[str, list[str]] = {
    "Python": [r"\bpython\b"],
    "Go": [
        r"\bgolang\b",
        r"\busing\s+go\b",
        r"\bgo\s*(?:,|/|\+|;|\bor\b|\band\b)",
        r"\b(?:python|java|javascript|typescript|c\+\+|react)\s+or\s+go\b",
        r"\bgo\s+or\s+similar\s+languages?\b",
    ],
    "C++": [r"(?<!\w)c\+\+(?!\w)"],
    "Java": [r"\bjava\b"],
    "Kotlin": [r"\bkotlin\b"],
    "JavaScript": [r"\bjavascript\b", r"(?<!\.)\bjs\b"],
    "TypeScript": [r"\btypescript\b", r"(?<!\.)\bts\b"],
    "React": [r"\breact(?:\.js)?\b"],
    "Next.js": [r"\bnext(?:\.js|js)?\b"],
    "Node.js": [
        r"\bnode\.js\b",
        r"\bnodejs\b",
        r"\bnode\s+js\b",
        r"\bnode\s+(?:backend|apis?|services?|servers?|runtime|applications?|apps?|microservices?)\b",
        r"\b(?:react|express|javascript|typescript)\s*/\s*node\b",
        r"\bnode\s*/\s*(?:react|express|javascript|typescript)\b",
    ],
    "FastAPI": [r"\bfastapi\b"],
    "Django": [r"\bdjango\b"],
    "Flask": [r"\bflask\b"],
    "SQL": [r"\bsql\b"],
    "PostgreSQL": [r"\bpostgresql\b", r"\bpostgres\b"],
    "MySQL": [r"\bmysql\b"],
    "MongoDB": [r"\bmongodb\b", r"\bmongo\b"],
    "Redis": [r"\bredis\b"],
    "NoSQL": [r"\bnosql\b", r"\bno-sql\b"],
    "Snowflake": [r"\bsnowflake\b"],
    "Docker": [r"\bdocker\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "AWS": [r"\baws\b", r"\bamazon web services\b"],
    "Azure": [r"\bazure\b"],
    "GCP": [r"\bgcp\b", r"\bgoogle cloud\b"],
    "Git": [r"\bgit\b", r"\bgithub\b", r"\bgitlab\b"],
    "CI/CD": [r"\bci/cd\b", r"\bcontinuous integration\b", r"\bcontinuous delivery\b"],
    "REST API": [r"\brest(?:ful)? api(?:s)?\b", r"\bapis?\b", r"\brest\b"],
    "API Design": [r"\bapi design\b", r"\bdesign(?:ing)? apis?\b", r"\bapi architecture\b"],
    "GraphQL": [r"\bgraphql\b"],
    "Linux": [r"\blinux\b", r"\bunix\b"],
    "Data Structures": [r"\bdata structures?\b"],
    "Software Engineering Fundamentals": [r"\bprogramming fundamentals\b", r"\btechnical foundation\b"],
    "PySpark": [r"\bpyspark\b"],
    "Pandas": [r"\bpandas\b"],
    "NumPy": [r"\bnumpy\b"],
    "Polars": [r"\bpolars\b"],
    "Terraform": [r"\bterraform\b"],
    "Temporal": [r"\btemporal\b"],
    "TensorFlow": [r"\btensorflow\b"],
    "PyTorch": [r"\bpytorch\b"],
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b"],
    "Computer Vision": [r"\bcomputer vision\b"],
    "HTML": [r"\bhtml\b"],
    "CSS": [r"\bcss\b"],
    "Tailwind CSS": [r"\btailwind(?: css)?\b"],
    "Android Development": [r"\bandroid development\b", r"\bandroid apps?\b", r"\bandroid applications?\b"],
    "Agile": [r"\bagile\b"],
    "Scrum": [r"\bscrum\b"],
    "JIRA": [r"\bjira\b"],
    "Unit Testing": [r"\bunit testing\b", r"\bunit tests?\b", r"\bunit\s+and\s+integration\s+tests?\b"],
    "Integration Testing": [r"\bintegration testing\b", r"\bintegration tests?\b"],
    "Test Automation": [r"\btest automation\b", r"\bautomated tests?\b", r"\bautomated testing\b"],
    "HIPAA": [r"\bhipaa\b"],
    "Healthcare Compliance": [r"\bhealthcare compliance\b", r"\bhealth care compliance\b", r"\bhipaa compliance\b"],
    "AI": [r"\bai\b", r"\bartificial intelligence\b"],
    "AI Agents": [r"\bai agents?\b", r"\bagentic ai\b"],
    "Backend": [r"\bbackend\b", r"\bback[- ]end\b"],
    "Backend Systems": [
        r"\bbackend systems?\b",
        r"\bscalable backend services?\b",
        r"\bcore platform capabilities\b",
    ],
    "Distributed Systems": [r"\bdistributed systems?\b", r"\bdistributed architecture\b"],
    "Observability": [r"\bobservability\b", r"\bmonitoring and alerting\b", r"\bmetrics and tracing\b"],
    "Production Debugging": [
        r"\bproduction debugging\b",
        r"\bdebug(?:ging)? production\b",
        r"\bdebug(?:ging)? production issues\b",
    ],
    "Performance": [r"\bperformance tuning\b", r"\blow latency\b", r"\bhigh throughput\b", r"\bquery performance\b", r"\bsystem performance\b"],
    "Reliability": [r"\breliability\b", r"\bresilien(?:ce|cy)\b", r"\bfault tolerance\b"],
    "Cloud Infrastructure": [r"\bcloud infrastructure\b", r"\binfrastructure as code\b", r"\bplatform infrastructure\b"],
    "Event-driven Systems": [r"\bevent[- ]driven systems?\b", r"\bevent[- ]driven architecture\b", r"\bevent streams?\b"],
    "Async Processing": [r"\basync processing\b", r"\basynchronous processing\b", r"\bbackground jobs?\b", r"\bjob queues?\b"],
    "Forward Deployed Engineering": [r"\bforward deployed engineer(?:ing)?\b", r"\bforward-deployed engineer(?:ing)?\b"],
    "Customer-Facing Engineering": [
        r"\bcustomer[- ]facing engineering\b",
        r"\bcustomer[- ]facing engineer\b",
        r"\bwork directly with customers\b",
        r"\bcustomer stakeholders?\b",
        r"\bcustomer success\b",
        r"\bimplementation/configuration\b",
    ],
    "Quantitative Modeling": [r"\bquantitative modeling\b", r"\bquant models?\b", r"\bfinancial modeling\b"],
    "Forecasting": [r"\bforecasting\b", r"\bforecasts?\b"],
    "Optimization": [r"\boptimization\b", r"\boptimisation\b"],
    "LLM Workflows": [r"\bllm workflows?\b", r"\bllm-powered workflows?\b", r"\blarge language model workflows?\b"],
    "Data Pipelines": [r"\bdata pipelines?\b", r"\betl\b", r"\bdata ingestion\b"],
    "Product Management": [r"\bproduct manager\b", r"\bproduct management\b"],
    "Healthcare": [
        r"\bhealthcare\s+(?:workflows?|systems?|platforms?|products?|software|data|operations|providers?|clinics?|patients?)\b",
        r"\bhealth care\s+(?:workflows?|systems?|platforms?|products?|software|data|operations|providers?|clinics?|patients?)\b",
        r"\bclinical workflows?\b",
        r"\bpatients?\b",
        r"\bclinics?\b",
        r"\bproviders?\b",
        r"\bmedical records?\b",
        r"\bcare delivery\b",
    ],
    "Health-tech": [r"\bhealth[- ]?tech\b", r"\bdigital health\b"],
    "Startup": [r"\bstartup\b", r"\bstart-up\b", r"\bseed stage\b", r"\bearly stage\b"],
    "Nontraditional Work": [
        r"\bflexible schedule\b",
        r"\bchoose projects?\b",
        r"\bhourly pay\b",
        r"\bpaypal\b",
        r"\bassessment[- ]based onboarding\b",
        r"\bpaid work becomes available\b",
        r"\balongside a full[- ]time role\b",
        r"\bavailability\b.{0,40}\bcountry\b",
        r"\bremote coding tasks?\b.{0,80}\bai models?\b",
    ],
    "Staffing/Training Placement": [
        r"\bopt/cpt\b",
        r"\bopt\b.{0,20}\bcpt\b",
        r"\bpre[- ]job training\b",
        r"\bassignments?\b.{0,40}\btraining\b",
        r"\bcase studies\b.{0,40}\btraining\b",
        r"\bmock sessions?\b",
        r"\bmultiple interview rounds?\b.{0,80}\bclients?\b",
        r"\bdifferent clients?\b",
        r"\bclient'?s project\b",
        r"\bclient project\b",
        r"\bsponsorship\b.{0,80}\bclient'?s project\b",
        r"\bsponsorship\b.{0,80}\bclient project\b",
        r"\bplacement\b.{0,40}\btraining\b",
    ],
}

DOMAIN_SIGNAL_LABELS = {
    "AI",
    "AI Agents",
    "Healthcare",
    "Health-tech",
    "Startup",
    "Product Management",
    "Nontraditional Work",
    "Staffing/Training Placement",
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

BENEFITS_SECTION_PATTERNS = [
    r"benefits?",
    r"what we offer",
    r"compensation",
    r"target salary range",
    r"perks?",
    r"health insurance",
    r"medical,?\s+dental",
]

LEGAL_SECTION_PATTERNS = [
    r"equal opportunity",
    r"eeo",
    r"legal",
    r"disclaimer",
    r"privacy",
    r"compliance notice",
]

INTERVIEW_SECTION_PATTERNS = [
    r"interview process",
    r"hiring process",
    r"recruiting process",
]

ROLE_SECTION_PATTERNS = [
    r"about the role",
    r"what you'll do",
    r"what you will do",
    r"responsibilities",
    r"technical foundation",
    r"the role",
    r"our stack",
    r"tools for the job",
    r"tech stack",
    r"who you are",
]


@dataclass(frozen=True)
class SignalRule:
    label: str
    pattern: str
    polarity: str
    severity: int = 1


EXPERIENCE_RULES = [
    SignalRule("new grad", r"\bnew grad(?:uate)?s?\b", "positive", 3),
    SignalRule("exceptional new grads encouraged", r"\bexceptional new grad(?:uate)?s?\b.{0,40}\bencouraged to apply\b", "positive", 3),
    SignalRule("entry-level", r"\bentry[- ]level\b", "positive", 3),
    SignalRule("junior", r"\bjunior\b", "positive", 2),
    SignalRule("early career", r"\bearly career\b", "positive", 2),
    SignalRule("eager to learn", r"\beager to learn\b|\bmotivated\b.{0,40}\bjunior\b", "positive", 2),
    SignalRule("mentorship", r"\bmentorship\b|\bmentoring\b|\blearn from senior developers\b|\blearn from senior engineers\b", "positive", 2),
    SignalRule("willing to grow", r"\bwilling to grow\b|\bgrowth mindset\b", "positive", 1),
    SignalRule("bachelor degree", r"\bbachelor'?s degree\b.{0,60}\b(?:completed|progress|in progress)\b|\bcompleted\b.{0,60}\bbachelor'?s degree\b", "positive", 1),
    SignalRule("support role", r"\bsupport role\b|\bassist(?:ing)? in (?:designing|building|developing)\b", "positive", 1),
    SignalRule("university graduate", r"\buniversity graduate\b|\bcollege graduate\b|\brecent graduate\b", "positive", 3),
    SignalRule("internship", r"\binternship\b|\bintern\b", "positive", 1),
    SignalRule("0-1 years", r"\b0\s*(?:-|–|\bto\b)\s*1\s+years?\b", "positive", 3),
    SignalRule("0-2 years", r"\b0\s*(?:-|–|\bto\b)\s*2\s+years?\b", "positive", 3),
    SignalRule("1+ years", r"\b1\s*\+\s+years?\b|\bat least 1 year\b|\bminimum 1 year\b|\b1 or more years?\b", "positive", 2),
    SignalRule("2+ years", r"\b2\s*\+\s+years?\b|\bat least 2 years\b|\bminimum 2 years\b|\b2 or more years?\b", "mixed", 1),
    SignalRule("1-4 years", r"\b1\s*(?:-|–|\bto\b)\s*4\s+years?\b", "mixed", 1),
    SignalRule("3+ years", r"\b3\s*\+\s+years?\b|\bat least 3 years\b|\bminimum 3 years\b|\b3 or more years?\b", "negative", 2),
    SignalRule("5+ years", r"\b5\s*\+\s+years?\b|\bat least 5 years\b|\bminimum 5 years\b|\b5 or more years?\b", "negative", 3),
    SignalRule("senior", r"\bsenior\b|\bsr\.\b", "negative", 3),
    SignalRule("senior team", r"\bsenior team\b|\bsmall,?\s+senior team\b", "negative", 3),
    SignalRule("staff", r"\bstaff\b", "negative", 3),
    SignalRule("principal", r"\bprincipal\b", "negative", 3),
    SignalRule("lead", r"\blead engineer\b|\blead developer\b|\blead scoped engagements?\b|\blead technical\b", "negative", 3),
    SignalRule("architect", r"\barchitect\b", "negative", 3),
    SignalRule("high ownership", r"\bhigh degree of ownership\b|\bhigh ownership\b|\bown(?:ership)? .* end[- ]to[- ]end\b", "negative", 2),
    SignalRule("independent ownership", r"\bindependently own\b|\bindependent ownership\b|\bown scoped engagements?\b", "negative", 2),
    SignalRule("mentor junior teammates", r"\bmentor junior teammates\b|\bmentor junior developers\b|\bmentor junior engineers\b", "negative", 2),
    SignalRule("work directly with CTO", r"\bwork directly with (?:the )?cto\b", "negative", 2),
    SignalRule("all rounder", r"\ball[- ]rounder\b|\ball rounder\b", "negative", 2),
    SignalRule("5 days a week in person", r"\b5 days a week\b.{0,50}\bin person\b|\bin person\b.{0,50}\b5 days a week\b", "negative", 2),
    SignalRule("6 days a week", r"\b6 days a week\b|\bsix days a week\b", "negative", 3),
    SignalRule("production-ready product in 2 days", r"\bproduction[- ]ready\b.{0,80}\binstagram\b.{0,80}\b2 days\b|\binstagram\b.{0,80}\b2 days\b", "negative", 3),
    SignalRule("many roles in one", r"\binsanely good product manager, designer, and backend/ai engineer all in one\b|\bproduct manager\b.{0,80}\bdesigner\b.{0,80}\bbackend/ai engineer\b", "negative", 3),
    SignalRule("significant revenue", r"\bbuilt and scaled\b.{0,80}\bsignificant revenue\b|\bsignificant revenue\b", "negative", 3),
    SignalRule("early stage startup experience", r"\bearly stage startup experience\b|\bseed stage startup\b|\bstartup intensity\b", "negative", 2),
]

AUTHORIZATION_POSITIVE_PATTERNS = [
    r"\bsponsor(?:s|ship)?\b.{0,40}\b(h-?1b|visa|opt|cpt)\b",
    r"\b(h-?1b|visa|opt|cpt)\b.{0,40}\bsponsor",
    r"\bvisa sponsorship is available\b",
    r"\bauthorized to work in (?:the )?(?:united states|u\.?s\.?|us)\b",
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
