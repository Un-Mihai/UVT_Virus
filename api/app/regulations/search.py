"""Finding the regulation passages that matter for a document, in pgvector."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import RegulationDocument, RegulationPassage


@dataclass(frozen=True)
class Passage:
    id: int
    regulation_document_id: int
    filename: str
    page: int
    text: str


class PassageSearch(Protocol):
    """What the compliance agent needs from the regulation store; tests can fake it."""

    async def nearest(self, vector: Sequence[float], limit: int) -> list[Passage]: ...

    async def in_order(self, limit_chars: int) -> list[Passage]: ...

    async def has_passages(self) -> bool: ...


class PgvectorPassageSearch:
    """Searches the passages of the given regulation documents by cosine distance.

    Only vectors made by `model` are compared; regulations embedded with another model (or not
    at all) are still reachable through `in_order`, the fallback without embeddings.
    """

    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        regulation_ids: Sequence[int],
        model: str,
    ) -> None:
        self._sessions = sessions
        self._ids = list(regulation_ids)
        self._model = model

    def _select(self) -> Select[RegulationPassage, str]:
        return (
            select(RegulationPassage, RegulationDocument.filename)
            .join(
                RegulationDocument,
                RegulationDocument.id == RegulationPassage.regulation_document_id,
            )
            .where(RegulationPassage.regulation_document_id.in_(self._ids))
        )

    async def nearest(self, vector: Sequence[float], limit: int) -> list[Passage]:
        if not self._ids:
            return []
        query = (
            self._select()
            .where(
                RegulationPassage.embedding.is_not(None),
                RegulationPassage.embedding_model == self._model,
                func.vector_dims(RegulationPassage.embedding) == len(vector),
            )
            .order_by(RegulationPassage.embedding.cosine_distance(list(vector)))
            .limit(limit)
        )
        async with self._sessions() as session:
            rows = (await session.execute(query)).all()
        return [_passage(row[0], row[1]) for row in rows]

    async def in_order(self, limit_chars: int) -> list[Passage]:
        """The regulations from their start, up to `limit_chars` of text."""
        if not self._ids:
            return []
        query = self._select().order_by(
            RegulationPassage.regulation_document_id, RegulationPassage.page, RegulationPassage.id
        )
        async with self._sessions() as session:
            rows = (await session.execute(query)).all()
        taken: list[Passage] = []
        used = 0
        for passage, filename in rows:
            used += len(passage.text)
            if used > limit_chars and taken:
                break
            taken.append(_passage(passage, filename))
        return taken

    async def has_passages(self) -> bool:
        if not self._ids:
            return False
        async with self._sessions() as session:
            found = await session.scalar(
                self._select().with_only_columns(RegulationPassage.id).limit(1)
            )
        return found is not None


def _passage(row: RegulationPassage, filename: str) -> Passage:
    return Passage(row.id, row.regulation_document_id, filename, row.page, row.text)
