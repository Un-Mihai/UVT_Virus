"""Starts and finishes verification runs: the only module that writes runs and findings."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import DocumentFinding, DocumentPage, ProjectDocument, VerificationRun
from app.personal_data import IdentifierHasher
from app.verification.context import VerificationContext, load_context
from app.verification.findings import ResolvedFinding
from app.verification.orchestrator import VerificationOrchestrator
from app.vocabulary import RunStatus, Scope

logger = logging.getLogger(__name__)

# shortcut: runs execute in the API process (BackgroundTasks); a restart loses the run in
# flight, which then reads as failed after this long. Move to a job queue if runs get long.
STALE_AFTER = timedelta(minutes=30)


def is_stale(run: VerificationRun) -> bool:
    unfinished = run.status in (RunStatus.PENDING, RunStatus.RUNNING)
    return unfinished and datetime.now(UTC) - run.created_at > STALE_AFTER


async def run_verification(
    sessions: async_sessionmaker[AsyncSession],
    orchestrator: VerificationOrchestrator,
    hasher: IdentifierHasher,
    embedding_model: str,
    run_id: int,
) -> None:
    """Background entrypoint: never raises, records the outcome on the run instead."""
    async with sessions() as session:
        run = await session.get_one(VerificationRun, run_id)
        run.status = RunStatus.RUNNING
        project_id, scope = run.project_id, Scope(run.scope)
        await session.commit()
    try:
        async with sessions() as session:
            context = await load_context(
                session, sessions, project_id, scope, hasher, embedding_model
            )
            findings = await orchestrator.run(context)
            await _save_cache(session, context)
            session.add_all(_rows(run_id, scope, findings))
            await _finish(session, run_id, RunStatus.COMPLETED, None)
    except Exception as error:
        logger.exception("Verification run %s failed", run_id)
        async with sessions() as session:
            await _finish(session, run_id, RunStatus.FAILED, f"{type(error).__name__}: {error}")


async def _save_cache(session: AsyncSession, context: VerificationContext) -> None:
    for document in context.documents:
        await session.execute(
            update(ProjectDocument)
            .where(ProjectDocument.id == document.id)
            .values(document_type=document.document_type)
        )
        for page in document.pages:
            if page.facts_changed and page.facts is not None:
                await session.execute(
                    update(DocumentPage)
                    .where(DocumentPage.id == page.id)
                    .values(facts=page.facts.model_dump(), facts_version=page.facts_version)
                )


def _rows(run_id: int, scope: Scope, findings: list[ResolvedFinding]) -> list[DocumentFinding]:
    rows = []
    for resolved in findings:
        draft, evidence = resolved.draft, resolved.draft.evidence
        rows.append(
            DocumentFinding(
                run_id=run_id,
                scope=scope,
                rule_code=draft.rule_code,
                agent=draft.agent,
                severity=draft.severity,
                confidence=resolved.confidence,
                reason=draft.reason,
                recommendation=draft.recommendation,
                document_id=evidence.document_id if evidence else None,
                page=evidence.page if evidence else None,
                quote=(evidence.quote or None) if evidence else None,
                rects=[list(rect) for rect in resolved.rects],
                ocr=resolved.ocr,
                regulation_document_id=draft.regulation.document_id if draft.regulation else None,
                regulation_page=draft.regulation.page if draft.regulation else None,
                regulation_quote=draft.regulation.quote if draft.regulation else None,
            )
        )
    return rows


async def _finish(session: AsyncSession, run_id: int, status: RunStatus, error: str | None) -> None:
    await session.execute(
        update(VerificationRun)
        .where(VerificationRun.id == run_id)
        .values(status=status, error=error, finished_at=datetime.now(UTC))
    )
    await session.commit()
