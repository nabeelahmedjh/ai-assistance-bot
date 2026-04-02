from django.db import models
from pgvector.django import VectorField


class Document(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    source_type = models.CharField(max_length=64, default='manual')
    file_url = models.URLField(blank=True, default='')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.title


class Chunk(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chunks',
    )
    content = models.TextField()
    embedding = VectorField(dimensions=384)
    chunk_index = models.PositiveIntegerField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['document_id', 'chunk_index']
        unique_together = ('document', 'chunk_index')

    def __str__(self) -> str:
        return f'{self.document_id}:{self.chunk_index}'


class ConversationTurn(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
    )

    lead_id = models.CharField(max_length=128, db_index=True)
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    message = models.TextField()
    intent = models.CharField(max_length=32, default='general')
    response_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f'{self.lead_id}:{self.role}:{self.created_at.isoformat()}'
