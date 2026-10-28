"""Small helpers the checks share."""

import re

from app.romanian import normalize_ro
from app.verification.context import RuleView
from app.verification.findings import CERTAIN, Evidence, FindingDraft
from app.verification.messages import Param, message

LEGAL_FORMS = {"srl", "sa", "snc", "scs", "sca", "pfa", "ii", "if", "srld"}


def finding(
    rule: RuleView, key: str, evidence: Evidence | None = None, **params: Param
) -> FindingDraft:
    """A deterministic finding: certain, with the rule's own severity and a catalog message."""
    reason, recommendation = message(key, **params)
    return FindingDraft(
        rule_code=rule.code,
        agent="checks",
        severity=rule.severity,
        confidence=CERTAIN,
        reason=reason,
        recommendation=recommendation,
        evidence=evidence,
    )


def cui_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def company_key(name: str) -> str:
    """'ALFA CONSTRUCT S.R.L.' and 'Alfa Construct SRL' compare equal."""
    words = re.findall(r"\w+", normalize_ro(name).casefold().replace(".", ""))
    return " ".join(word for word in words if word not in LEGAL_FORMS)
