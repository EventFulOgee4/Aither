from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, generics, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import TherapySession, ChatMessage, MoodEntry
from .serializers import TherapySessionSerializer, ChatMessageSerializer, MoodEntrySerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied



# Simple AI response stub (replace with real AI later)
def get_ai_response(user_message):
    return "Thank you for sharing that. Can you tell me more?"

class TherapySessionViewSet(viewsets.ModelViewSet):
    serializer_class = TherapySessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = TherapySession.objects.filter(user=self.request.user)
        title = self.request.query_params.get('title')
        if title:
            queryset = queryset.filter(title__icontains=title)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ChatMessage.objects.filter(session__user=self.request.user)
        session_id = self.request.query_params.get('session')
        if session_id:
            queryset = queryset.filter(session__id=session_id)
        return queryset

    def perform_create(self, serializer):
        session = serializer.validated_data['session']

        # Ownership check
        if session.user != self.request.user:
            raise PermissionDenied("Not your session")

        # Save user message
        self.user_message = serializer.save(sender="user")

        # Generate AI message
        self.ai_message = ChatMessage.objects.create(
            session=session,
            sender="ai",
            message=get_ai_response(self.user_message.message)
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "user_message": ChatMessageSerializer(self.user_message).data,
            "ai_message": ChatMessageSerializer(self.ai_message).data
        }, status=201)

        

@api_view(['GET'])
def test_api(request):
    return Response({"status": "ok", "message": "API is working"})


class MoodEntryViewSet(viewsets.ModelViewSet):
    serializer_class = MoodEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = MoodEntry.objects.filter(user=self.request.user).order_by('-created_at')
        session_id = self.request.query_params.get('session')
        if session_id:
            queryset = queryset.filter(session__id=session_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)