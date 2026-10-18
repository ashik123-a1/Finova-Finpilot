"""
Core Domain Exceptions for SME Finance Copilot.
"""

class CopilotException(Exception):
    """Base exception for all SME Finance Copilot domain errors."""
    pass


class ShopAccessDeniedError(CopilotException):
    """Raised when an unauthorized actor attempts cross-shop access."""
    pass


class FinancialPrecisionError(CopilotException):
    """Raised when monetary amounts violate precision rules or exceed limits."""
    pass


class InconsistentFinancialRecordError(CopilotException):
    """Raised when financial figures do not balance (e.g. sum(items) != total)."""
    pass


class DocumentProcessingError(CopilotException):
    """Raised when an uploaded document fails validation, classification, or extraction."""
    pass


class DuplicateDocumentError(DocumentProcessingError):
    """Raised when a document with identical content hash is uploaded."""
    pass


class LowConfidenceExtractionError(DocumentProcessingError):
    """Raised when OCR/extraction falls below the safe automatic posting threshold."""
    pass


class ResourceNotFoundError(CopilotException):
    """Raised when a requested database entity is not found."""
    pass
