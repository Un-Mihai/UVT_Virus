from app.verification.checks import run_check
from app.verification.context import VerificationContext
from app.verification.findings import FindingDraft
from app.vocabulary import RuleKind


class DeterministicChecksAgent:
    """Runs the scope's rules of kind "check" through the check registry. No AI involved."""

    name = "checks"

    async def run(self, context: VerificationContext) -> list[FindingDraft]:
        return [
            finding
            for rule in context.rules_of(RuleKind.CHECK)
            for finding in run_check(context, rule)
        ]
