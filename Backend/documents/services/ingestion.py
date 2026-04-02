from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import List

from django.db import transaction
from sentence_transformers import SentenceTransformer

from documents.models import Chunk, Document


EMBEDDING_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
EMBEDDING_DIMENSIONS = 384


@dataclass(frozen=True)
class ChunkPayload:
    content: str
    chunk_index: int
    metadata: dict


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def chunk_text(content: str, chunk_size: int = 500, overlap: int = 100) -> List[ChunkPayload]:
    """
    Use a sliding window with overlap so adjacent chunks preserve context at boundaries.
    This improves retrieval quality for questions that reference details split across lines.
    """
    normalized = ' '.join(content.split())
    if not normalized:
        return []

    chunks: List[ChunkPayload] = []
    start = 0
    index = 0
    step = max(1, chunk_size - overlap)

    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        segment = normalized[start:end].strip()
        if segment:
            chunks.append(
                ChunkPayload(
                    content=segment,
                    chunk_index=index,
                    metadata={
                        'start_char': start,
                        'end_char': end,
                        'chunk_size': chunk_size,
                        'overlap': overlap,
                    },
                )
            )
            index += 1
        start += step

    return chunks


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []

    model = get_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return [vector.tolist() for vector in vectors]


@transaction.atomic
def ingest_document(document_id: int, chunk_size: int = 500, overlap: int = 100) -> int:
    document = Document.objects.select_for_update().get(pk=document_id)
    payloads = chunk_text(document.content, chunk_size=chunk_size, overlap=overlap)

    Chunk.objects.filter(document=document).delete()

    if not payloads:
        document.processed = True
        document.save(update_fields=['processed'])
        return 0

    embeddings = generate_embeddings([item.content for item in payloads])

    chunk_rows = [
        Chunk(
            document=document,
            content=item.content,
            embedding=embedding,
            chunk_index=item.chunk_index,
            metadata=item.metadata,
        )
        for item, embedding in zip(payloads, embeddings)
    ]

    Chunk.objects.bulk_create(chunk_rows)
    document.processed = True
    document.save(update_fields=['processed'])
    return len(chunk_rows)
