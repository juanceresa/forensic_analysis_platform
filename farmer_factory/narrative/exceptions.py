"""Exceptions for narrative generation."""


class NarrativeGenerationError(Exception):
    """Base exception for narrative generation errors."""
    pass


class SessionCostLimitExceeded(NarrativeGenerationError):
    """Raised when session cost exceeds limit."""

    def __init__(self, session_id: str, current_cost: float, limit: float):
        self.session_id = session_id
        self.current_cost = current_cost
        self.limit = limit
        super().__init__(
            f"Session {session_id} exceeded cost limit: "
            f"${current_cost:.2f} > ${limit:.2f}"
        )


class InsufficientGraphData(NarrativeGenerationError):
    """Raised when constellation has insufficient data."""
    pass
