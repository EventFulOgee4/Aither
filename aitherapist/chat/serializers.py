from rest_framework import serializers
from .models import TherapySession, ChatMessage

class TherapySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapySession
        fields = ['id', 'title', 'created_at']

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'sender', 'message', 'timestamp']
        read_only_fields = ['sender', 'timestamp']


