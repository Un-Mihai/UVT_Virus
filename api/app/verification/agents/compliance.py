"""Finds where the documents break the regulations, with retrieval (RAG) over the passages.

For each document, the pages are embedded and the nearest regulation passages are retrieved
(app/regulations/search.py); the model compares the document with those passages and with the
admins' written rules, and reports discrepancies that cite both sides. One more review looks at
the application as a whole (a missing document, say). When a requirement needs arithmetic or an
identifier checked, the model asks for a code check instead of judging it; those run here.
"""

import asyncio
import dataclasses
import json
import logging
import re
import unicodedata
from decimal import Decimal

import openai
from pydantic import BaseModel

from app.ai.client import AIClient, AINotConfiguredError, AIResponseError, BudgetExceededError
from app.personal_data import MaskedText, mask_for_model
from app.regulations.chunking import split_pages
from app.regulations.search import Passage
from app.romanian import quote_in_page, quote_key
from app.verification.checks import InvalidCheckError, list_checks, run_check
from app.verification.context import DocumentView, RuleView, VerificationContext
from app.verification.findings import Evidence, FindingDraft, RegulationRef
from app.vocabulary import Severity

logger = logging.getLogger(__name__)

PASSAGES_PER_PAGE = 4
QUERY_CHARS = 4000  # of each page, to embed as a search query
START_CHARS = 1500  # of a long document's first page, shown with its later excerpts
EMBEDDING_ERRORS = (AINotConfiguredError, BudgetExceededError, AIResponseError, openai.APIError)
# Words that oblige, without diacritics. A list of data an institution collects, or a model
# form's sample text, has none of them, so a finding resting on it is dropped.
OBLIGATION = re.compile(
    r"\b(?:trebuie|oblig\w*|impun\w*|interzis\w*|nu (?:poate|pot)|necesar\w*|"
    r"se (?:completeaza|solicita|cere|prezinta|depune|anexeaza|mentioneaza|inscrie|intocmeste)|"
    r"cel (?:putin|mult)|maxim\w*|minim\w*|valabil\w*|"
    r"must|shall|required?|requires|mandatory|at least|at most|no more than)\b"
)

COMMON = """- `applies_because`: who the passage or rule is addressed to (which kind of document, from
  which issuer) and why this one falls under it; `applies`: false when it does not, and the
  item is dropped. Fill these in first;
- `mandatory_because`: the exact words of the passage that impose the obligation;
  `mandatory`: false when the passage only allows or describes, and the item is dropped.
  Data an institution may or can process, collect, consult or request is a permission, not
  something this document must contain. The fill-in text of a model form (dots, brackets, "de
  completat", sample values) is a template: it states no requirement and may itself be wrong;
- `source`: the id of the passage (like P12) or the code of the written rule broken;
- `regulation_quote`: the exact words of that passage stating the requirement ("" for a rule);
- reason and recommendation in English (reason_en, recommendation_en) and in Romanian
  (reason_ro, recommendation_ro), saying the same thing;
- severity: "bad" for a definite breach, "warn" when a person should look; confidence 0 to 1.
When a requirement needs arithmetic (sums, totals, VAT), comparing dates or validating an
identifier (CUI, IBAN, CNP), do not judge it yourself: add a request to `checks` with a check_id
from CODE CHECKS, its params as a JSON object in text ("{}" when it takes none), and its source.
Report only what a passage or rule actually requires; return empty lists when nothing is wrong.
A passage applies only when it states a requirement on this kind of document from this issuer.
It does not apply when it describes what a bank or an authority processes, lists categories of
data, rights or definitions, sets the duties of another institution (one bank's rules for its
own statements do not bind another bank's), is one bank's own general conditions, product
page or information note (it binds that bank's own forms, never a document issued by another
institution, whatever the file name of the passage says), tells what another document must
contain (an information notice, a contract) when this one only confirms or refers to it,
governs another form or procedure, or concerns accreditation, administrators or an
authority's internal work.
A value in a field of the document is wrong only when a passage states a rule that value
breaks. A value that is unusual, fictional or unlike a model form's sample is not a finding.
When unsure, do not report.
Text like [CNP#1a2b3c] is a placeholder this system put where the document has a personal
identifier: the document does contain a value there, and equal placeholders are equal values.
Never report a placeholder as missing, masked, hidden or incomplete."""

DOCUMENT_INSTRUCTIONS = f"""You check ONE document of a funding application against the
regulation passages and written rules given, and report its discrepancies: places where the
document breaks or contradicts what a passage or rule requires of it, or leaves out something
it requires. You see the pages under "--- page n ---" lines (of a long document, its start for
context and then the part to check): something stated on another page, such as a period, a
header or a total, is not missing. You see text only: signatures, stamps, logos and handwriting
are images, so never report them as missing or unclear, and ignore notices that mark the
document as a specimen, a test or fictional. For each give:
- page and `quote`: the exact text from that page of the document;
{COMMON}"""

APPLICATION_INSTRUCTIONS = f"""You check a funding application as a whole against the
regulation passages and written rules given, and report only problems no single page shows:
a document they require that is missing, or a requirement the application form breaks.
The form stores a CNP only masked and has company fields (CUI, legal representative) that stay
empty for a private person: an empty or masked form field is not a finding. Report what a
passage requires of this application, not what it requires of another form, a bank or an
authority. For each issue give:
{COMMON}"""


class CheckRequest(BaseModel):
    check_id: str
    params: str  # a JSON object as text: strict structured output allows no free-form objects
    source: str


class Discrepancy(BaseModel):
    applies_because: str  # written before the verdict, so the model weighs it first
    applies: bool
    mandatory_because: str  # the passage's own words that impose the obligation
    mandatory: bool
    page: int
    quote: str
    source: str
    regulation_quote: str
    reason_en: str
    reason_ro: str
    recommendation_en: str
    recommendation_ro: str
    severity: str
    confidence: float


class DocumentReview(BaseModel):
    discrepancies: list[Discrepancy]
    checks: list[CheckRequest]


class ApplicationIssue(BaseModel):
    applies_because: str
    applies: bool
    mandatory_because: str
    mandatory: bool
    source: str
    regulation_quote: str
    reason_en: str
    reason_ro: str
    recommendation_en: str
    recommendation_ro: str
    severity: str
    confidence: float


class ApplicationReview(BaseModel):
    issues: list[ApplicationIssue]
    checks: list[CheckRequest]


@dataclasses.dataclass(frozen=True)
class Source:
    """What a finding is reported against: a written rule, or a regulation passage."""

    rule: RuleView
    passage: Passage | None

    def citation(self, quote: str) -> RegulationRef | None:
        if self.passage is None:
            return None
        exact = quote if quote and quote_in_page(quote, self.passage.text) else None
        return RegulationRef(self.passage.regulation_document_id, self.passage.page, exact)


class RegulationComplianceAgent:
    name = "compliance"

    def __init__(self, ai: AIClient, concurrency: int, context_chars: int) -> None:
        self._ai = ai
        self._limit = asyncio.Semaphore(concurrency)
        self._passage_chars = context_chars // 3
        self._document_chars = context_chars // 2

    async def run(self, context: VerificationContext) -> list[FindingDraft]:
        if not context.rules and not await context.passages.has_passages():
            return []  # nothing to check against: no regulation and no written rule applies
        documents = [doc for doc in context.documents if any(p.text.strip() for p in doc.pages)]
        reviews = await asyncio.gather(
            self._review_application(context),
            *(self._review_document(context, document) for document in documents),
        )
        drafts = [draft for found, _ in reviews for draft in found]
        requests = [request for _, asked in reviews for request in asked]
        return drafts + _run_checks(context, requests)

    async def _review_document(
        self, context: VerificationContext, document: DocumentView
    ) -> tuple[list[FindingDraft], list[tuple[CheckRequest, Source]]]:
        reviews = await asyncio.gather(
            *(
                self._review_excerpt(context, document, chunks, later=index > 0)
                for index, chunks in enumerate(_excerpts(document, self._document_chars))
            )
        )
        return (
            [draft for drafts, _ in reviews for draft in drafts],
            [request for _, requests in reviews for request in requests],
        )

    async def _review_excerpt(
        self,
        context: VerificationContext,
        document: DocumentView,
        chunks: list[tuple[int, str]],
        later: bool,
    ) -> tuple[list[FindingDraft], list[tuple[CheckRequest, Source]]]:
        queries = [mask_for_model(text[:QUERY_CHARS], context.hasher).text for _, text in chunks]
        passages = await self._retrieve(context, queries)
        body = "\n\n".join(f"--- page {number} ---\n{text}" for number, text in chunks)
        masked = mask_for_model(body, context.hasher)
        start = ""
        if later and document.pages:  # who issued a long document is on its first page
            head = mask_for_model(document.pages[0].text[:START_CHARS], context.hasher).text
            start = f"START OF THE DOCUMENT (context only, report nothing on it):\n{head}\n\n"
        sources = _sources(context, passages)
        review = await self._ask(
            DOCUMENT_INSTRUCTIONS,
            [
                _passages_section(passages),
                _rules_section(context),
                _checks_section(),
                f"APPLICATION FORM:\n{json.dumps(context.form, ensure_ascii=False)}",
                f"DOCUMENT {document.id}: {document.filename} "
                f"({document.document_type or 'unknown type'})\n{start}{masked.text}",
            ],
            DocumentReview,
            purpose=f"compliance document {document.id}",
        )
        drafts = [
            draft
            for item in review.discrepancies
            if (draft := _discrepancy(document, item, masked, sources)) is not None
        ]
        return drafts, _requests(review.checks, sources)

    async def _review_application(
        self, context: VerificationContext
    ) -> tuple[list[FindingDraft], list[tuple[CheckRequest, Source]]]:
        listing = "\n".join(
            f"- document {doc.id}: {doc.filename} ({doc.document_type or 'unknown type'}), "
            f"{len(doc.pages)} pages"
            for doc in context.documents
        )
        form = json.dumps(context.form, ensure_ascii=False)
        query = f"Required documents, eligibility and conditions.\n{form}\n{listing}"
        passages = await self._retrieve(context, [query], per_query=PASSAGES_PER_PAGE * 3)
        sources = _sources(context, passages)
        review = await self._ask(
            APPLICATION_INSTRUCTIONS,
            [
                _passages_section(passages),
                _rules_section(context),
                _checks_section(),
                f"APPLICATION FORM:\n{form}",
                f"DOCUMENTS UPLOADED:\n{listing or '(none)'}",
            ],
            ApplicationReview,
            purpose="compliance application",
        )
        drafts = []
        for issue in review.issues:
            source = sources.get(issue.source)
            if (
                not (issue.applies and issue.mandatory)
                or source is None
                or not _obliges(source, issue.mandatory_because)
                or not _valid_source_quote(source, issue.regulation_quote)
            ):
                continue  # a finding must rest on a requirement that was actually given
            drafts.append(
                _draft(
                    source, issue, evidence=None, citation=source.citation(issue.regulation_quote)
                )
            )
        return drafts, _requests(review.checks, sources)

    async def _retrieve(
        self, context: VerificationContext, queries: list[str], per_query: int = PASSAGES_PER_PAGE
    ) -> list[Passage]:
        """The passages nearest to the queries; the regulations' start when search cannot run."""
        found: dict[int, Passage] = {}
        try:
            vectors = await self._ai.embed(purpose="find regulation passages", texts=queries)
        except EMBEDDING_ERRORS:
            vectors = []
        for vector in vectors:
            for passage in await context.passages.nearest(vector, per_query):
                found.setdefault(passage.id, passage)
        if not found:
            return await context.passages.in_order(self._passage_chars)
        taken: list[Passage] = []
        used = 0
        for passage in found.values():
            used += len(passage.text)
            if used > self._passage_chars and taken:
                break
            taken.append(passage)
        return taken

    async def _ask[T: BaseModel](
        self, instructions: str, sections: list[str], schema: type[T], purpose: str
    ) -> T:
        async with self._limit:
            return await self._ai.complete(
                purpose=purpose,
                messages=[
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": "\n\n".join(sections)},
                ],
                schema=schema,
            )


def _excerpts(document: DocumentView, limit: int) -> list[list[tuple[int, str]]]:
    """The page chunks (a page, or part of a long one), consecutive ones packed together up to
    `limit` characters, so a page is judged with the pages around it."""
    groups: list[list[tuple[int, str]]] = []
    used = 0
    for chunk in split_pages(((page.number, page.text) for page in document.pages), limit):
        if groups and used + len(chunk[1]) <= limit:
            groups[-1].append(chunk)
        else:
            groups.append([chunk])
            used = 0
        used += len(chunk[1])
    return groups


def _sources(context: VerificationContext, passages: list[Passage]) -> dict[str, Source]:
    """Every label the model may cite: passage ids (P12) and written rule codes."""
    sources = {rule.code: Source(rule, None) for rule in context.rules}
    for passage in passages:
        rule = RuleView(
            code=f"{passage.filename} p.{passage.page}",
            title=passage.filename,
            description=passage.text,
            severity=Severity.BAD,
        )
        sources[f"P{passage.id}"] = Source(rule, passage)
    return sources


def _passages_section(passages: list[Passage]) -> str:
    if not passages:
        return "REGULATION PASSAGES:\n(none uploaded)"
    body = "\n\n".join(
        f"[P{passage.id}] {passage.filename}, page {passage.page}:\n{passage.text}"
        for passage in passages
    )
    return f"REGULATION PASSAGES:\n{body}"


def _rules_section(context: VerificationContext) -> str:
    if not context.rules:
        return "WRITTEN RULES:\n(none)"
    body = "\n".join(f"[{rule.code}] {rule.title}: {rule.description}" for rule in context.rules)
    return f"WRITTEN RULES:\n{body}"


def _checks_section() -> str:
    lines = [
        f"- {spec.id}: {spec.description['en']} Params schema: "
        f"{json.dumps(spec.params_model.model_json_schema().get('properties', {}))}"
        for spec in list_checks()
    ]
    return "CODE CHECKS:\n" + "\n".join(lines)


def _requests(
    checks: list[CheckRequest], sources: dict[str, Source]
) -> list[tuple[CheckRequest, Source]]:
    return [(check, sources[check.source]) for check in checks if check.source in sources]


def _discrepancy(
    document: DocumentView,
    item: Discrepancy,
    masked: MaskedText,
    sources: dict[str, Source],
) -> FindingDraft | None:
    """The discrepancy as a finding; None when its quote or its source cannot be verified."""
    source = sources.get(item.source)
    page = document.page(item.page)
    quote = masked.restore(item.quote)
    if (
        not (item.applies and item.mandatory)
        or source is None
        or not _obliges(source, item.mandatory_because)
        or not _valid_source_quote(source, item.regulation_quote)
        or page is None
        or not quote_in_page(quote, page.text)
    ):
        return None
    return _draft(
        source,
        item,
        evidence=Evidence(document.id, item.page, quote),
        citation=source.citation(item.regulation_quote),
    )


def _obliges(source: Source, words: str) -> bool:
    """The model's `mandatory_because` must be the passage's own words, and they must oblige.
    A written rule is the admin's own wording: nothing to check."""
    # shortcut: a fixed list of obligation words, in Romanian and English. A rule worded
    # without any of them is dropped; add the word when a real requirement is missed.
    if source.passage is None:
        return True
    plain = "".join(
        char
        for char in unicodedata.normalize("NFD", quote_key(words))
        if not unicodedata.combining(char)
    )
    return quote_in_page(words, source.passage.text) and bool(OBLIGATION.search(plain))


def _valid_source_quote(source: Source, quote: str) -> bool:
    return source.passage is None or bool(
        quote.strip() and quote_in_page(quote, source.passage.text)
    )


def _draft(
    source: Source,
    item: Discrepancy | ApplicationIssue,
    evidence: Evidence | None,
    citation: RegulationRef | None,
) -> FindingDraft:
    severity = Severity(item.severity) if item.severity in Severity else source.rule.severity
    confidence = min(max(Decimal(str(item.confidence)), Decimal(0)), Decimal(1))
    return FindingDraft(
        rule_code=source.rule.code,
        agent="compliance",
        severity=severity,
        confidence=confidence.quantize(Decimal("0.001")),
        reason={"en": item.reason_en, "ro": item.reason_ro},
        recommendation={"en": item.recommendation_en, "ro": item.recommendation_ro},
        evidence=evidence,
        regulation=citation,
    )


def _run_checks(
    context: VerificationContext, requests: list[tuple[CheckRequest, Source]]
) -> list[FindingDraft]:
    """Each requested code check once, its findings cited to the passage that asked for it."""
    drafts: list[FindingDraft] = []
    done: set[tuple[str, str]] = set()
    for request, source in requests:
        try:
            params = json.loads(request.params or "{}")
            if not isinstance(params, dict):
                raise InvalidCheckError("params must be a JSON object")
            key = (request.check_id, json.dumps(params, sort_keys=True))
            if key in done:
                continue
            done.add(key)
            rule = dataclasses.replace(source.rule, code=request.check_id)
            found = run_check(context, rule, request.check_id, params)
        except (InvalidCheckError, ValueError) as error:
            logger.warning("Skipped check %s: %s", request.check_id, error)
            continue
        citation = source.citation("")
        drafts += [dataclasses.replace(draft, regulation=citation) for draft in found]
    return drafts
