from __future__ import annotations

from typing import Dict, List


SYSTEM_PROMPT = (
    'You are an AI sales assistant for Atlas Container Supply. '
    'Answer using only provided context when possible. '
    'Always cite sources using document titles, keep answers concise, '
    'and include a clear next sales step such as requesting zip code '
    'for delivered pricing or intended use for better recommendations.'
)


def build_prompt(query: str, context: List[Dict]) -> str:
    if not context:
        context_block = 'No relevant documentation was retrieved.'
    else:
        parts = []
        for idx, item in enumerate(context, start=1):
            parts.append(
                f"[{idx}] Source: {item['document_title']}\\n"
                f"Content: {item['content']}"
            )
        context_block = '\n\n'.join(parts)

    return (
        f"System:\n{SYSTEM_PROMPT}\n\n"
        f"Retrieved context:\n{context_block}\n\n"
        f"User question:\n{query}\n\n"
        'Return JSON with keys: answer, citations, next_step.'
    )
