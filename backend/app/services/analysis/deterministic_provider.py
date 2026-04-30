class DeterministicRuleBasedProvider:
    """Initial no-paid-AI analysis provider. Rules will be added in a later step."""

    def analyze(self, profile: object, job: object) -> object:
        raise NotImplementedError("Deterministic analysis is not implemented yet.")
