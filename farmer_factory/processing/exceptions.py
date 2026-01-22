"""Custom exceptions for processing pipeline."""


class ProcessingError(Exception):
    """
    Exception raised when document processing fails.

    Used to wrap errors from PDF loading, preprocessing, extraction,
    or graph building stages. Provides clear context about which
    document/stage failed for better error reporting.
    """
    pass
