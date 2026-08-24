class LeadProcessingError(Exception):
    """Base exception for safe lead-processing failures."""


class MissingAIResultError(LeadProcessingError):
    """Raised when lead creation is attempted without an AI result."""


class InvalidAIResultError(LeadProcessingError):
    """Raised when the AI result is invalid or belongs to another enquiry."""


class EnquiryNotReadyError(LeadProcessingError):
    """Raised when the enquiry is not ready for lead creation."""


class LeadPersistenceError(LeadProcessingError):
    """Raised when lead creation cannot be persisted safely."""


class InvalidLeadStatusTransitionError(LeadProcessingError):
    """Raised when a lead status transition is not allowed."""
