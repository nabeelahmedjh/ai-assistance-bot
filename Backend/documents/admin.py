from django.contrib import admin

from documents.models import Chunk, ConversationTurn, Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'source_type', 'processed', 'uploaded_at')
    list_filter = ('processed', 'source_type')
    search_fields = ('title', 'content')


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'chunk_index')
    list_filter = ('document',)
    search_fields = ('content',)


@admin.register(ConversationTurn)
class ConversationTurnAdmin(admin.ModelAdmin):
    list_display = ('id', 'lead_id', 'role', 'intent', 'created_at')
    list_filter = ('role', 'intent')
    search_fields = ('lead_id', 'message')
