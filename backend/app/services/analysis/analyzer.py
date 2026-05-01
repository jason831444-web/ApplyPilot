from app.models.job import Job
from app.models.profile import Profile
from app.services.analysis.deterministic_provider import DeterministicRuleBasedProvider
from app.services.analysis.provider import AnalysisProvider, JobAnalysisResult


class JobAnalyzer:
    """Coordinates the configured analysis provider."""

    def __init__(self, provider: AnalysisProvider | None = None) -> None:
        self.provider = provider or DeterministicRuleBasedProvider()

    def analyze(self, *, profile: Profile, job: Job) -> JobAnalysisResult:
        return self.provider.analyze(profile, job)
