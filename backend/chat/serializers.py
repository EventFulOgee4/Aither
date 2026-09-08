from rest_framework import serializers
from .models import TherapySession, ChatMessage, MoodEntry

class SessionOwnershipMixin:
    def validate_session(self, session):
        if session is not None and session.user_id != self.context['request'].user.id:
            raise serializers.ValidationError('Session not found.')
        return session


class StreamMessageSerializer(serializers.Serializer):
    session = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    message = serializers.CharField(max_length=2000, trim_whitespace=True)
    tone = serializers.ChoiceField(choices=['neutral', 'assertive', 'tender', 'empathy'], default='neutral')
#from django.contrib.auth.models import User

class TherapySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapySession
        fields = ['id', 'title', 'created_at', 'last_activity', 'message_count']
        read_only_fields = ['created_at', 'last_activity', 'message_count']

class ChatMessageSerializer(SessionOwnershipMixin, serializers.ModelSerializer):
    message = serializers.CharField(max_length=2000, trim_whitespace=True)
    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'sender', 'message', 'timestamp']
        read_only_fields = ['sender', 'timestamp']

class MoodEntrySerializer(SessionOwnershipMixin, serializers.ModelSerializer):
    intensity = serializers.IntegerField(min_value=1, max_value=10)
    class Meta:
        model = MoodEntry
        fields = '__all__'
        read_only_fields = ['user', 'created_at']
