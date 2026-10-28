from typing import Protocol

from app.verification.context import VerificationContext
from app.verification.findings import FindingDraft


class VerificationAgent(Protocol):
    """One step of a verification run. It may enrich the context for later stages (facts)."""

    name: str

    async def run(self, context: VerificationContext) -> list[FindingDraft]: ...
