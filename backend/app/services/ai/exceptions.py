class AIServiceError(Exception):
    """Base exception for AI-related failures."""


class AIProviderError(AIServiceError):
    """Raised when the AI provider fails."""


class AIProviderTimeout(AIServiceError):
    """Raised when the AI provider takes too long."""


class AIResponseValidationError(AIServiceError):
    """Raised when the AI response cannot be validated."""