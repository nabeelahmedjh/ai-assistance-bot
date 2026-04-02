from __future__ import annotations

from typing import Dict, List

from pgvector.django import CosineDistance

from documents.models import Chunk
from documents.services.ingestion import generate_embeddings


def retrieve_context(query: str, top_k: int = 3) -> List[Dict]:
    query_vector = generate_embeddings([query])[0]

    matches = (
        Chunk.objects.select_related('document')
        .annotate(distance=CosineDistance('embedding', query_vector))
        .order_by('distance')[:top_k]
    )

    return [
        {
            'chunk_id': chunk.id,
            'document_id': chunk.document_id,
            'document_title': chunk.document.title,
            'chunk_index': chunk.chunk_index,
            'content': chunk.content,
            'score': 1 - float(chunk.distance),
            'metadata': chunk.metadata,
        }
        for chunk in matches
    ]
