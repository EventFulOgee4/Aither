from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import ChatMessage
from .serializers import MessageSerializer
class ChatMessageViewSet(viewsets.ModelViewSet):
    queryset = ChatMessage.objects.all()
    serializer_class = MessageSerializer
