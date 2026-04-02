from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import TemplateView

from documents.models import Chunk, ConversationTurn, Document
from documents.serializers import (
    ChatRequestSerializer,
    ChunkSerializer,
    ConversationTurnSerializer,
    DocumentSerializer,
)
from documents.services.chat import classify_intent, generate_structured_reply
from documents.services.ingestion import ingest_document
from documents.services.prompting import build_prompt
from documents.services.retrieval import retrieve_context


class DocumentListCreateView(generics.ListCreateAPIView):
    queryset = Document.objects.all().order_by('-uploaded_at')
    serializer_class = DocumentSerializer

    def create(self, request, *args, **kwargs):
        is_bulk = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=is_bulk)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data if not is_bulk else {})
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class DocumentChunksView(generics.ListAPIView):
    serializer_class = ChunkSerializer

    def get_queryset(self):
        return Chunk.objects.filter(document_id=self.kwargs['pk']).order_by('chunk_index')


class DocumentIngestView(APIView):
    def post(self, request, pk):
        count = ingest_document(pk)
        return Response({'document_id': pk, 'chunks_created': count, 'processed': True})


class AIChatView(APIView):
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lead_id = serializer.validated_data['lead_id']
        message = serializer.validated_data['message']

        user_intent = classify_intent(message)
        ConversationTurn.objects.create(
            lead_id=lead_id,
            role='user',
            message=message,
            intent=user_intent,
        )

        context = retrieve_context(message, top_k=3)
        prompt = build_prompt(message, context)
        payload = generate_structured_reply(message, context, user_intent)
        payload['prompt_preview'] = prompt[:500]

        assistant_turn = ConversationTurn.objects.create(
            lead_id=lead_id,
            role='assistant',
            message=payload['answer'],
            intent=user_intent,
            response_payload=payload,
        )

        response_body = {
            'lead_id': lead_id,
            'message_id': assistant_turn.id,
            'response': payload,
        }
        return Response(response_body, status=status.HTTP_200_OK)


class ChatHistoryView(generics.ListAPIView):
    serializer_class = ConversationTurnSerializer

    def get_queryset(self):
        return ConversationTurn.objects.filter(lead_id=self.kwargs['lead_id']).order_by('created_at')


class WebSocketTestView(TemplateView):
    template_name = 'documents/ws_test.html'
