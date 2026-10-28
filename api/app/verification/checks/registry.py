"""Deterministic checks: the tools the compliance agent asks for when a requirement needs
arithmetic or an identifier validated, so code computes and the model only reads.

Adding a check: write a function in a module of this package, decorate it with
@register_check, and import the module in checks/__init__.py. The model is offered every
registered check, with its description and params schema, on the next run.
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


def validated_params(check_id: str, params: dict[str, Any]) -> BaseModel:
    """The params parsed for the check; InvalidCheckError when the check or params are wrong."""
    spec = _CHECKS.get(check_id)
    if spec is None:
        raise InvalidCheckError(f"Unknown check {check_id!r}.")
    try:
        return spec.params_model.model_validate(params)
    except ValidationError as error:
        raise InvalidCheckError(f"Invalid params for {check_id}: {error}") from error


def run_check(
    context: VerificationContext, rule: RuleView, check_id: str, params: dict[str, Any]
) -> list[FindingDraft]:
    """Findings of one check, reported against `rule`; InvalidCheckError for an unknown check."""
    parsed = validated_params(check_id, params)
    return _CHECKS[check_id].function(context, rule, parsed)
