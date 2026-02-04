from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, generics, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import TherapySession, ChatMessage, MoodEntry
from .serializers import TherapySessionSerializer, ChatMessageSerializer, MoodEntrySerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import permission_classes
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Min, Max
from django.db.models.functions import Length
from django.utils import timezone


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
        session.last_activity = user_message.timestamp
        session.message_count += 2  # user + AI
        session.save()

        # Ownership check
        if session.user != self.request.user:
            raise PermissionDenied("Not your session")

        # Save user message
        self.user_message = serializer.save(sender="user")

        # Update session activity
        session.last_activity = timezone.now()
        session.save(update_fields=["last_activity"])

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
@permission_classes([AllowAny])
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
        if mood.session:
            mood.session.last_activity = timezone.now()
            mood.session.save(update_fields=["last_activity"])
            
#Metadata view for a therapy session
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def session_metadata(request, session_id):
    """
    Returns detailed metadata for a single therapy session.
    Includes messages, AI responses, moods, and session stats.
    """
    try:
        # 1️⃣ Get the session owned by the current user
        session = TherapySession.objects.get(id=session_id, user=request.user)
    except TherapySession.DoesNotExist:
        return Response({"detail": "Session not found or not yours"}, status=404)

    # 2️⃣ Gather messages & moods
    messages = session.messages.all()  # related_name="messages"
    moods = session.moods.all()        # related_name="moods"

    # 3️⃣ Compute message stats
    user_message_count = messages.filter(sender='user').count()
    ai_message_count = messages.filter(sender='ai').count()
    last_activity = messages.last().timestamp if messages.exists() else None
    average_message_length = messages.aggregate(avg_len=Avg(Length('message')))['avg_len'] if messages.exists() else None

    # 4️⃣ Compute mood stats
    average_mood = moods.aggregate(avg=Avg('intensity'))['avg'] if moods.exists() else None
    min_mood_intensity = moods.aggregate(min=Min('intensity'))['min'] if moods.exists() else None
    max_mood_intensity = moods.aggregate(max=Max('intensity'))['max'] if moods.exists() else None
    mood_count = moods.count()

    # 5️⃣ Session-level stats
    session_duration_seconds = (messages.last().timestamp - session.created_at).total_seconds() if messages.exists() else 0

    # 6️⃣ Return metadata
    return Response({
        "session_id": session.id,
        "title": session.title,
        "created_at": session.created_at,
        "user_messages": user_message_count,
        "ai_messages": ai_message_count,
        "last_activity": last_activity,
        "average_message_length": average_message_length,
        "mood_count": mood_count,
        "average_mood": average_mood,
        "min_mood_intensity": min_mood_intensity,
        "max_mood_intensity": max_mood_intensity,
        "session_duration_seconds": session_duration_seconds
    })
