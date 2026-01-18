from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import TherapySession, ChatMessage
from .serializers import TherapySessionSerializer, ChatMessageSerializer

class TherapySessionViewSet(viewsets.ModelViewSet):
    queryset = TherapySession.objects.all()
    serializer_class = TherapySessionSerializer

class ChatMessageViewSet(viewsets.ModelViewSet):
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
