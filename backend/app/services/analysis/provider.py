from typing import Protocol


class AnalysisProvider(Protocol):
    def analyze(self, profile: object, job: object) -> object:
        """Analyze a job against a profile and return a structured result."""
        ...
