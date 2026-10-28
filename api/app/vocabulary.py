"""Values shared by the tables and the domain modules; stored as strings with CHECK constraints."""

from enum import StrEnum


class Scope(StrEnum):
    """Which verification process a rule, regulation, run or finding belongs to."""

    CLIENT = "client"
    REVIEWER = "reviewer"


class RuleKind(StrEnum):
    CHECK = "check"  # a deterministic Python check from app/verification/checks
    AI = "ai"  # a regulation clause judged by the compliance agent


class Severity(StrEnum):
    BAD = "bad"  # a definite error
    WARN = "warn"  # worth a look


class ProjectStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OcrStatus(StrEnum):
    """How a page without a text layer is being read; None on pages that have one."""

    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"  # no OCR engine configured


class Decision(StrEnum):
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"


def check_in(column: str, values: type[StrEnum]) -> str:
    """SQL for a CHECK constraint that limits `column` to the enum's values."""
    quoted = ", ".join(f"'{value}'" for value in values)
    return f"{column} IN ({quoted})"
