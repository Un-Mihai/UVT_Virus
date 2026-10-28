from dataclasses import dataclass
from decimal import Decimal

from app.auth import Role, User
from app.config import Settings
from app.vocabulary import Scope


@dataclass(frozen=True)
class Visibility:
    """The verification process a user works in, and the lowest confidence they are shown."""

    scope: Scope
    min_confidence: Decimal


def visibility_for(user: User, settings: Settings) -> Visibility | None:
    """Reviewers work in the reviewer scope, clients in the client scope, admins in neither."""
    if user.has_role(Role.REVIEWER):
        return Visibility(Scope.REVIEWER, settings.reviewer_confidence_threshold)
    if user.has_role(Role.CLIENT):
        return Visibility(Scope.CLIENT, settings.client_confidence_threshold)
    return None
