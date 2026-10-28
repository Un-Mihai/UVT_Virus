"""A project's list of documents to add: by default read from the client-scope regulations that
apply to it (every project, its type, the project itself) and the admins' written rules; an admin
can add, edit or delete items. The model quotes, code checks the quote (like the compliance agent).
"""

import logging

from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.client import AIClient
from app.config import Settings
from app.models import (
    Project,
    ProjectType,
    RegulationDocument,
    RegulationRule,
    RequiredDocument,
)
from app.regulations.levels import documents_for, rules_for
from app.regulations.processing import EMBEDDING_ERRORS
from app.regulations.search import Passage, PgvectorPassageSearch
from app.romanian import quote_in_page
from app.vocabulary import RequiredDocumentSource, Scope

logger = logging.getLogger(__name__)

PASSAGES = 20  # per query
# The regulations are mostly Romanian, so the search asks in both languages.
QUERIES = (
    "Documentele pe care solicitantul trebuie să le depună sau să le anexeze la cerere: acte de "
    "identitate, adeverințe, extrase, certificate, declarații, documente justificative.",
    "Documents the applicant must submit or attach to the application: identity documents, "
    "income statements, certificates, declarations, supporting documents.",
)
INSTRUCTIONS = """You list the documents an applicant must add to a funding application, using
only the regulation passages and written rules given, which come from many regulations: most
concern other matters, so first decide whether each one asks the applicant for a document.
For each document give:
- `applies_because`: who must provide it and why this kind of application needs it; `applies`:
  false when the passage is about something else (a bank's own duties or records, definitions,
  rights, data processing, another product), and the item is dropped. Fill these in first;
- `name`: what the applicant would call the document, short, with a capital letter, in the
  language of the passage ("Carte de identitate", "Adeverință de venit"). Never a legal phrase
  or a category such as "documente justificative" when the passage names a concrete document;
- `description`: one sentence in the same language: what it must contain or prove, its validity or
  form, when the passage says so ("" otherwise);
- `source`: the id of the passage (like P12) or the code of the written rule that requires it;
- `regulation_quote`: the exact words of that passage that require the document ("" for a rule).
Leave out what a bank or an authority produces itself (contracts, offers, notices), forms to
fill in and facts to declare. List each document once. When nothing is required, return an
empty list."""


class ListedDocument(BaseModel):
    applies_because: str  # written before the verdict, so the model weighs it first
    applies: bool
    name: str
    description: str
    source: str
    regulation_quote: str


class DocumentList(BaseModel):
    documents: list[ListedDocument]


async def read_regulations(
    sessions: async_sessionmaker[AsyncSession], ai: AIClient, settings: Settings, project_id: int
) -> None:
    """Replaces the project's items read from the regulations with a fresh reading; the items
    an admin wrote or edited stay. Raises the AI errors (the route answers them)."""
    async with sessions() as session:
        project = await session.get_one(Project, project_id)
        project_type = await session.get_one(ProjectType, project.project_type_id)
        regulation_ids = list(
            await session.scalars(
                select(RegulationDocument.id).where(
                    documents_for(project.id, project.project_type_id, Scope.CLIENT)
                )
            )
        )
        rules = list(
            await session.scalars(
                select(RegulationRule)
                .where(rules_for(project.project_type_id, Scope.CLIENT))
                .order_by(RegulationRule.project_type_id.nulls_first(), RegulationRule.id)
            )
        )
    kind = f"{project_type.name}. {project_type.description}".strip()
    search = PgvectorPassageSearch(sessions, regulation_ids, settings.ai_embedding_model)
    passages = await _passages(
        ai, search, regulation_ids, kind, settings.compliance_context_chars // 3
    )
    listed: list[ListedDocument] = []
    if passages or rules:
        answer = await ai.complete(
            purpose=f"required documents {project_id}",
            messages=[
                {"role": "system", "content": INSTRUCTIONS},
                {"role": "user", "content": _prompt(kind, passages, rules)},
            ],
            schema=DocumentList,
        )
        listed = answer.documents
    async with sessions() as session:
        await session.execute(
            delete(RequiredDocument).where(
                RequiredDocument.project_id == project_id,
                RequiredDocument.source == RequiredDocumentSource.REGULATIONS,
            )
        )
        kept = await session.scalars(
            select(RequiredDocument.name).where(RequiredDocument.project_id == project_id)
        )
        session.add_all(
            _verified(project_id, listed, passages, rules, {n.casefold() for n in kept})
        )
        await session.commit()


async def derive_required_documents(
    sessions: async_sessionmaker[AsyncSession], ai: AIClient, settings: Settings, project_id: int
) -> None:
    """The default list of a new project, in the background. Never raises: without a provider
    or regulations the list stays empty and an admin can read again or write it."""
    try:
        await read_regulations(sessions, ai, settings, project_id)
    except Exception:
        logger.exception("Reading the required documents of project %s failed", project_id)


async def _passages(
    ai: AIClient,
    search: PgvectorPassageSearch,
    regulation_ids: list[int],
    kind: str,
    limit_chars: int,
) -> list[Passage]:
    """The passages nearest to the queries about this kind of project; the regulations' start
    when search cannot run."""
    if not regulation_ids:
        return []
    found: dict[int, Passage] = {}
    try:
        vectors = await ai.embed(
            purpose="find required documents", texts=[f"{kind}\n{query}" for query in QUERIES]
        )
        for vector in vectors:
            for passage in await search.nearest(vector, PASSAGES):
                found.setdefault(passage.id, passage)
    except EMBEDDING_ERRORS:
        found = {}
    return list(found.values()) or await search.in_order(limit_chars)


def _prompt(kind: str, passages: list[Passage], rules: list[RegulationRule]) -> str:
    texts = "\n\n".join(f"[P{p.id}] {p.filename}, page {p.page}:\n{p.text}" for p in passages)
    written = "\n".join(f"[{rule.code}] {rule.title}: {rule.description}" for rule in rules)
    return (
        f"APPLICATION: {kind}\n\nREGULATION PASSAGES:\n{texts or '(none)'}"
        f"\n\nWRITTEN RULES:\n{written or '(none)'}"
    )


def _verified(
    project_id: int,
    listed: list[ListedDocument],
    passages: list[Passage],
    rules: list[RegulationRule],
    taken: set[str],
) -> list[RequiredDocument]:
    """The listed documents as rows; one that does not apply, whose source was not given, whose
    quote is not in its passage, or whose name repeats an earlier one is dropped."""
    by_label = {f"P{passage.id}": passage for passage in passages}
    codes = {rule.code for rule in rules}
    rows: list[RequiredDocument] = []
    for item in listed:
        name = item.name.strip()
        passage = by_label.get(item.source)
        grounded = (passage is not None and quote_in_page(item.regulation_quote, passage.text)) or (
            passage is None and item.source in codes
        )
        if not item.applies or not name or name.casefold() in taken or not grounded:
            continue
        taken.add(name.casefold())
        rows.append(
            RequiredDocument(
                project_id=project_id,
                name=name,
                description=item.description.strip(),
                source=RequiredDocumentSource.REGULATIONS,
                regulation_document_id=passage.regulation_document_id if passage else None,
                regulation_page=passage.page if passage else None,
                regulation_quote=item.regulation_quote.strip() if passage else None,
            )
        )
    return rows
