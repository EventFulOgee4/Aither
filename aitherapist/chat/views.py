from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, generics, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import TherapySession, ChatMessage
from .serializers import TherapySessionSerializer, ChatMessageSerializer

class TherapySessionViewSet(viewsets.ModelViewSet):
    #queryset = TherapySession.objects.all()
    serializer_class = TherapySessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return TherapySession.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ChatMessageViewSet(viewsets.ModelViewSet):
    #queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return ChatMessage.objects.filter(session__user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(sender="user")

@api_view(['GET'])
def test_api(request):
    return Response({"status": "ok", "message": "API is working"})