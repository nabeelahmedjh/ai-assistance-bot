from __future__ import annotations

from typing import Dict, List


def classify_intent(message: str) -> str:
    text = message.lower()
    if any(token in text for token in ['price', 'cost', 'quote', 'how much']):
        return 'pricing'
    if any(token in text for token in ['deliver', 'delivery', 'available', 'stock']):
        return 'availability'
    if any(token in text for token in ['buy', 'order', 'invoice', 'purchase']):
        return 'conversion'
    return 'general'


def generate_structured_reply(query: str, context: List[Dict], intent: str) -> Dict:
    citations = [
        {
            'document_id': item['document_id'],
            'document_title': item['document_title'],
            'chunk_id': item['chunk_id'],
            'score': round(item['score'], 4),
        }
        for item in context
    ]

    if not context:
        return {
            'answer': (
                "I don't have enough matching documentation to answer confidently yet. "
                'If you share your container size and delivery zip code, I can prepare a fast quote.'
            ),
            'citations': citations,
            'next_step': 'Collect size, condition, and zip code for quoting.',
            'intent': intent,
            'handoff': intent == 'conversion',
        }

    best = context[0]
    answer = (
        f"Based on {best['document_title']}, {best['content']} "
        'I can also compare one-trip vs cargo-worthy and provide delivered pricing.'
    )

    if intent == 'pricing':
        next_step = 'Ask for delivery zip code to provide exact delivered quote.'
    elif intent == 'availability':
        next_step = 'Confirm destination zip and requested size to check live yard stock.'
    elif intent == 'conversion':
        next_step = 'Collect contact details and issue invoice-ready quote.'
    else:
        next_step = 'Ask intended use to recommend best container and add-ons.'

    return {
        'answer': answer,
        'citations': citations,
        'next_step': next_step,
        'intent': intent,
        'handoff': intent == 'conversion',
    }
