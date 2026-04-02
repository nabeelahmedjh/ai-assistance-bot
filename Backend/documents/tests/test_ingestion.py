from unittest.mock import patch

from django.test import TestCase

from documents.models import Document
from documents.services.ingestion import chunk_text, generate_embeddings


class IngestionServiceTests(TestCase):
    def test_chunk_creation(self):
        doc = Document.objects.create(
            title="Pricing",
            content="40ft standard container: $3,850. 20ft: $2,100. Delivery depends on zip.",
        )

        chunks = chunk_text(doc.content, chunk_size=40, overlap=10)

        self.assertGreater(len(chunks), 0)
        self.assertTrue(all(chunk.content for chunk in chunks))
        self.assertEqual(chunks[0].metadata["chunk_size"], 40)

    @patch("documents.services.ingestion.get_embedding_model")
    def test_embedding_similarity(self, mock_get_model):
        class _Vector(list):
            def tolist(self):
                return list(self)

        class _Model:
            def encode(self, texts, normalize_embeddings=True):
                return [
                    _Vector([1.0, 0.0, 0.0]),
                    _Vector([0.95, 0.05, 0.0]),
                ]

        mock_get_model.return_value = _Model()

        emb1, emb2 = generate_embeddings(
            ["shipping container prices", "container pricing information"]
        )

        dot = sum(a * b for a, b in zip(emb1, emb2))
        mag1 = sum(a * a for a in emb1) ** 0.5
        mag2 = sum(b * b for b in emb2) ** 0.5
        cosine_similarity = dot / (mag1 * mag2)

        self.assertGreater(cosine_similarity, 0.5)
