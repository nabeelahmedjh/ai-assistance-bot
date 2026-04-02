from django.contrib import admin

from documents.models import Chunk, Document


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
