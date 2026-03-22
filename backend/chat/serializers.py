from rest_framework import serializers
from .models import TherapySession, ChatMessage, MoodEntry
#from django.contrib.auth.models import User

class TherapySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapySession
        fields = ['id', 'title', 'created_at']

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'sender', 'message', 'timestamp']
        read_only_fields = ['timestamp']

class MoodEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MoodEntry
        fields = '__all__'
        read_only_fields = ['user', 'created_at']
