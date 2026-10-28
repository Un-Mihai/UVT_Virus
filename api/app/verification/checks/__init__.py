"""Deterministic checks. Importing this package registers every check module below."""

from app.verification.checks import (  # noqa: F401 (imported to register their checks)
    amounts,
    completeness,
    dates,
    form_consistency,
    identifiers,
    personal_data,
)
from app.verification.checks.registry import (
    CheckSpec,
    InvalidCheckError,
    list_checks,
    run_check,
    validated_params,
)

__all__ = ["CheckSpec", "InvalidCheckError", "list_checks", "run_check", "validated_params"]
