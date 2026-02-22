from rest_framework import serializers
from .models import ChatSession, ChatMessage, MoodEntry


class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ["id", "title", "created_at"]


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "emotion", "confidence", "avatar_state", "created_at"]


class MoodEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MoodEntry
        fields = ["id", "mood", "intensity", "note", "ai_inferred", "ai_emotion", "ai_confidence", "created_at"]
        read_only_fields = ["id", "ai_inferred", "ai_emotion", "ai_confidence", "created_at"]