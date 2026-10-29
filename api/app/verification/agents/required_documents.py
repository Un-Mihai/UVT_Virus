"""Reports each item of the project's list of documents to add that has no upload.

It runs as the orchestrator's gate: an incomplete file gets only these findings and nothing
else is checked, so no document is read or sent to a model until the file is complete.
"""

from app.verification.context import VerificationContext
from app.verification.findings import CERTAIN, FindingDraft
from app.verification.messages import message
from app.vocabulary import Severity

RULE_CODE = "completeness.required_document_missing"  # the web app recognises it by this code


class RequiredDocumentsAgent:
    name = "completeness"

    async def run(self, context: VerificationContext) -> list[FindingDraft]:
        drafts = []
        for item in context.required_documents:
            if not item.has_document:
                reason, recommendation = message("required_document_missing", document=item.name)
                drafts.append(
                    FindingDraft(
                        rule_code=RULE_CODE,
                        agent=self.name,
                        severity=Severity.BAD,
                        confidence=CERTAIN,
                        reason=reason,
                        recommendation=recommendation,
                    )
                )
        return drafts
