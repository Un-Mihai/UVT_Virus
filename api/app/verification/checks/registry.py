"""Deterministic checks, addressable by id from a rule (`RegulationRule.check_id`).

Adding a check: write a function in a module of this package, decorate it with
@register_check, and import the module in checks/__init__.py. Admins can then use its id.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from app.localized import LocalizedText
from app.verification.context import RuleView, VerificationContext
from app.verification.findings import FindingDraft


class NoParams(BaseModel):
    pass


type CheckFunction[P: BaseModel] = Callable[[VerificationContext, RuleView, P], list[FindingDraft]]


@dataclass(frozen=True)
class CheckSpec:
    id: str
    description: LocalizedText
    params_model: type[BaseModel]
    function: CheckFunction[Any]


class InvalidCheckError(ValueError):
    pass


_CHECKS: dict[str, CheckSpec] = {}


def register_check[P: BaseModel](
    check_id: str, description: LocalizedText, params: type[P]
) -> Callable[[CheckFunction[P]], CheckFunction[P]]:
    def decorate(function: CheckFunction[P]) -> CheckFunction[P]:
        if check_id in _CHECKS:
            raise RuntimeError(f"Check {check_id} is registered twice.")
        _CHECKS[check_id] = CheckSpec(check_id, description, params, function)
        return function

    return decorate


def list_checks() -> list[CheckSpec]:
    return sorted(_CHECKS.values(), key=lambda spec: spec.id)


def validated_params(check_id: str | None, params: dict[str, Any]) -> BaseModel:
    """The rule's params parsed for its check; raises InvalidCheckError for the admin to fix."""
    spec = _CHECKS.get(check_id or "")
    if spec is None:
        raise InvalidCheckError(f"Unknown check {check_id!r}. GET /api/checks lists them.")
    try:
        return spec.params_model.model_validate(params)
    except ValidationError as error:
        raise InvalidCheckError(f"Invalid params for {check_id}: {error}") from error


def run_check(context: VerificationContext, rule: RuleView) -> list[FindingDraft]:
    params = validated_params(rule.check_id, rule.params)
    return _CHECKS[rule.check_id or ""].function(context, rule, params)
