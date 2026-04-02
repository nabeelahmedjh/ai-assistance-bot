from django.urls import path

from documents.views import (
    AIChatView,
    ChatHistoryView,
    DocumentChunksView,
    DocumentIngestView,
    DocumentListCreateView,
)

urlpatterns = [
    path('documents/', DocumentListCreateView.as_view(), name='documents-list-create'),
    path('documents/<int:pk>/ingest/', DocumentIngestView.as_view(), name='documents-ingest'),
    path('documents/<int:pk>/chunks/', DocumentChunksView.as_view(), name='documents-chunks'),
    path('ai/chat/', AIChatView.as_view(), name='ai-chat'),
    path('ai/chat/history/<str:lead_id>/', ChatHistoryView.as_view(), name='ai-chat-history'),
]
