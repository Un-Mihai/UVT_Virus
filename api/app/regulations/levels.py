"""Which regulations and written rules apply to a project: those for every project, those for
its project type, and those attached to the project itself (one verification scope at a time)."""

from sqlalchemy import ColumnElement, and_, or_

from app.models import RegulationDocument, RegulationRule
from app.vocabulary import Scope


def documents_for(project_id: int, project_type_id: int, scope: Scope) -> ColumnElement[bool]:
    return and_(
        RegulationDocument.verification_scope == scope,
        or_(
            and_(
                RegulationDocument.project_type_id.is_(None),
                RegulationDocument.project_id.is_(None),
            ),
            RegulationDocument.project_type_id == project_type_id,
            RegulationDocument.project_id == project_id,
        ),
    )


def rules_for(project_type_id: int, scope: Scope) -> ColumnElement[bool]:
    """Written rules exist for every project or for a type, never for a single project."""
    return and_(
        RegulationRule.verification_scope == scope,
        RegulationRule.active,
        or_(
            RegulationRule.project_type_id.is_(None),
            RegulationRule.project_type_id == project_type_id,
        ),
    )
