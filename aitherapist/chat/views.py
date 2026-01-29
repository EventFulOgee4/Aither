from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, generics, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import TherapySession, ChatMessage, MoodEntry
from .serializers import TherapySessionSerializer, ChatMessageSerializer, MoodEntrySerializer


class TherapySessionViewSet(viewsets.ModelViewSet):
    serializer_class = TherapySessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return TherapySession.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# class ChatMessageViewSet(viewsets.ModelViewSet):
#     serializer_class = ChatMessageSerializer
#     permission_classes = [permissions.IsAuthenticated]
#     def get_queryset(self):
#         return ChatMessage.objects.filter(session__user=self.request.user)
#     def perform_create(self, serializer):
#         serializer.save(sender="user")

class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ChatMessage.objects.filter(
            session__user=self.request.user
        )

        session_id = self.request.query_params.get("session")
        if session_id:
            queryset = queryset.filter(session_id=session_id)

        return queryset

    def perform_create(self, serializer):
        user_message = serializer.save(sender="user")

        ai_text = get_ai_response(user_message.message)

        ChatMessage.objects.create(
            session=user_message.session,
            sender="ai",
            message=ai_text
        )

        

@api_view(['GET'])
def test_api(request):
    return Response({"status": "ok", "message": "API is working"})

#AI
def get_ai_response(user_message):
    return "Thank you for sharing that. Can you tell me more?"

class MoodEntryViewSet(viewsets.ModelViewSet):
    serializer_class = MoodEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MoodEntry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)