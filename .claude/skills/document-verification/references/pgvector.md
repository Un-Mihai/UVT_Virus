# pgvector with SQLAlchemy and Alembic

Tested against PostgreSQL 17 + pgvector 0.8 with the repo's stack. The `vector` extension is
created by the first migration; on Azure, Terraform allow-lists it (`azure.extensions = VECTOR`).

## Models

```python
from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str]
    sha256: Mapped[str] = mapped_column(String(64), unique=True)


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    page: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    # Must equal AI_EMBEDDING_DIMENSIONS (1536 for text-embedding-3-small).
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))

    __table_args__ = (
        Index(
            "ix_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
```

## Query

```python
from sqlalchemy import select

query_vector = (await ai.embed(purpose="search", texts=[question]))[0]
distance = Chunk.embedding.cosine_distance(query_vector)
rows = (
    await session.execute(
        select(Chunk.document_id, Chunk.page, Chunk.text, distance.label("distance"))
        .order_by(distance)
        .limit(8)
    )
).all()
```

Filter by document or project in the same `select` (`where(Chunk.document_id.in_(ids))`); keep
the page so answers can cite it.

## Migration notes

- `alembic revision --autogenerate` writes the column as `pgvector.sqlalchemy.vector.VECTOR(dim=1536)`
  but not the import: add `import pgvector.sqlalchemy` at the top of that migration.
- Check the generated index has `postgresql_using="hnsw"` and the `vector_cosine_ops` operator
  class; add them by hand if autogenerate dropped them.
- HNSW and IVFFlat indexes on `vector` support up to 2,000 dimensions. For
  `text-embedding-3-large` (3,072), request `dimensions=1536` or store `halfvec`.
- Changing the embedding model or dimensions means re-embedding every chunk: store the model name
  next to the vectors if you expect to switch.

## Keyword search alongside vectors

Exact identifiers (CUI, contract numbers) are found better by text than by embeddings. PostgreSQL
ships a `romanian` text-search configuration:
`to_tsvector('romanian', text) @@ websearch_to_tsquery('romanian', :q)`. Normalise diacritics
first (see romanian-data.md) so `ş` and `ș` match.
