"""
Utility functions for Farmer Factory.
Shared helpers for logging, file operations, and validation.
"""

import re
from pathlib import Path

# Pattern for validating case IDs to prevent path traversal attacks
# Allows alphanumeric characters, underscores, and hyphens
CASE_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]+$')


def validate_case_id(case_id: str) -> bool:
    """
    Validate case ID to prevent path traversal attacks.

    Args:
        case_id: The case identifier to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_case_id("TEST-CERESA")
        True
        >>> validate_case_id("../etc/passwd")
        False
        >>> validate_case_id("case/../admin")
        False
    """
    if not case_id:
        return False
    return bool(CASE_ID_PATTERN.match(case_id))


def get_safe_case_path(case_id: str, base_dir: Path = None) -> Path:
    """
    Get a safe path for a case directory, preventing path traversal.

    Args:
        case_id: The case identifier
        base_dir: Base directory for cases (defaults to 'cases')

    Returns:
        Resolved Path to the case directory

    Raises:
        ValueError: If case_id is invalid or path traversal is detected
    """
    if not validate_case_id(case_id):
        raise ValueError(f"Invalid case_id: {case_id}")

    if base_dir is None:
        base_dir = Path("cases")
    else:
        base_dir = Path(base_dir)

    resolved_base = base_dir.resolve()
    case_path = (base_dir / case_id).resolve()

    # Additional check: ensure resolved path is under the base directory
    try:
        case_path.relative_to(resolved_base)
    except ValueError:
        raise ValueError(f"Invalid case_id: path traversal detected")

    return case_path


__all__ = ["validate_case_id", "get_safe_case_path", "CASE_ID_PATTERN"]
