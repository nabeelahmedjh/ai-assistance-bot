from rest_framework import serializers

from documents.models import Chunk, ConversationTurn, Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'content',
            'source_type',
            'file_url',
            'uploaded_at',
            'processed',
        ]
        read_only_fields = ['id', 'uploaded_at', 'processed']


class ChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chunk
        fields = ['id', 'document', 'content', 'chunk_index', 'metadata']


class ChatRequestSerializer(serializers.Serializer):
    lead_id = serializers.CharField(max_length=128)
    message = serializers.CharField()


class ConversationTurnSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationTurn
        fields = [
            'id',
            'lead_id',
            'role',
            'message',
            'intent',
            'response_payload',
            'created_at',
        ]
