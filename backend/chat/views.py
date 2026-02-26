import time
from django.utils import timezone
from django.db.models import Avg, Min, Max
from django.db.models.functions import Length

from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied

from .models import TherapySession, ChatMessage, MoodEntry, AIInteraction
from .serializers import TherapySessionSerializer, ChatMessageSerializer, MoodEntrySerializer


# ----------------------------
# Optional ML brain (lazy load)
# ----------------------------
_brain_instance = None
_brain_error = None

def get_brain():
    """
    Lazy-load ML brain so Django can boot even if ML deps/modules are missing.
    """
    global _brain_instance, _brain_error

    if _brain_instance is not None:
        return _brain_instance
    if _brain_error is not None:
        return None

    try:
        from ml.brain import AitherBrain
        _brain_instance = AitherBrain()
        return _brain_instance
    except Exception as e:
        _brain_error = e
        print("⚠️ ML brain disabled:", e)
        return None


def fallback_ai_response(user_message: str) -> str:
    return "Thanks for sharing. I’m here with you — tell me more."


class TherapySessionViewSet(viewsets.ModelViewSet):
    serializer_class = TherapySessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = TherapySession.objects.filter(user=self.request.user)
        title = self.request.query_params.get("title")
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

        session_id = self.request.query_params.get("session")
        if session_id:
            queryset = queryset.filter(session__id=session_id)

        sender = self.request.query_params.get("sender")
        if sender:
            queryset = queryset.filter(sender=sender)

        return queryset

    def perform_create(self, serializer):
        session = serializer.validated_data["session"]

        # Ownership check
        if session.user != self.request.user:
            raise PermissionDenied("Not your session")

        # Save user message
        self.user_message = serializer.save(sender="user")

        # Generate AI response
        start = time.time()
        brain = get_brain()

        if brain is None:
            ai_text = fallback_ai_response(self.user_message.message)
            model_name = "fallback"
        else:
            try:
                ai_text = brain.respond(self.user_message.message)
                model_name = "aither-brain"
            except Exception as e:
                print("⚠️ brain.respond failed:", e)
                ai_text = fallback_ai_response(self.user_message.message)
                model_name = "fallback"

        latency_ms = int((time.time() - start) * 1000)

        # Save AI message
        self.ai_message = ChatMessage.objects.create(
            session=session,
            sender="ai",
            message=ai_text
        )

        # Update session metadata
        session.last_activity = timezone.now()
        if session.message_count is None:
            session.message_count = 0
        session.message_count += 2  # user + ai
        session.save(update_fields=["last_activity", "message_count"])

        # Log interaction
        AIInteraction.objects.create(
            session=session,
            model_name=model_name,
            prompt=self.user_message.message,
            response=ai_text,
            latency_ms=latency_ms
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        return Response(
            {
                "user_message": ChatMessageSerializer(self.user_message).data,
                "ai_message": ChatMessageSerializer(self.ai_message).data,
            },
            status=201,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def test_api(request):
    return Response({"status": "ok", "message": "API is working"})


class MoodEntryViewSet(viewsets.ModelViewSet):
    serializer_class = MoodEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = MoodEntry.objects.filter(user=self.request.user).order_by("-created_at")
        session_id = self.request.query_params.get("session")
        if session_id:
            queryset = queryset.filter(session__id=session_id)
        return queryset

    def perform_create(self, serializer):
        mood = serializer.save(user=self.request.user)
        if mood.session:
            mood.session.last_activity = timezone.now()
            mood.session.save(update_fields=["last_activity"])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_metadata(request, session_id):
    """
    Returns detailed metadata for a single therapy session.
    Includes messages, AI responses, moods, and session stats.
    """
    try:
        session = TherapySession.objects.get(id=session_id, user=request.user)
    except TherapySession.DoesNotExist:
        return Response({"detail": "Session not found or not yours"}, status=404)

    messages = session.messages.all()
    moods = session.moods.all()

    user_message_count = messages.filter(sender="user").count()
    ai_message_count = messages.filter(sender="ai").count()
    last_activity = messages.last().timestamp if messages.exists() else None
    average_message_length = (
        messages.aggregate(avg_len=Avg(Length("message")))["avg_len"]
        if messages.exists()
        else None
    )

    average_mood = moods.aggregate(avg=Avg("intensity"))["avg"] if moods.exists() else None
    min_mood_intensity = moods.aggregate(min=Min("intensity"))["min"] if moods.exists() else None
    max_mood_intensity = moods.aggregate(max=Max("intensity"))["max"] if moods.exists() else None
    mood_count = moods.count()

    session_duration_seconds = (
        (messages.last().timestamp - session.created_at).total_seconds()
        if messages.exists()
        else 0
    )

    return Response(
        {
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
            "session_duration_seconds": session_duration_seconds,
        }
    )