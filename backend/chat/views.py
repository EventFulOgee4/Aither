import time
from functools import lru_cache

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


@lru_cache(maxsize=1)
def get_engine():
    """
    Load the ML engine once per Django process.

    Prefer loader (real model integration). Fall back to AitherBrain if present.
    """
    try:
        from ml.loader import get_model
        models = get_model()
        if isinstance(models, dict):
            print("✅ ML engine: loader loaded. Keys:", list(models.keys()))
        else:
            print("✅ ML engine: loader loaded (non-dict):", type(models))
        return {"mode": "loader", "models": models}
    except Exception as e:
        print("⚠️ ml.loader.get_model not available:", repr(e))

    try:
        from ml.brain import AitherBrain
        brain = AitherBrain()
        print("✅ ML engine: AitherBrain loaded:", type(brain))
        return {"mode": "brain", "brain": brain}
    except Exception as e:
        print("⚠️ AitherBrain not available:", repr(e))

    print("❌ ML engine: none (will use fallback)")
    return {"mode": "none"}


def fallback_ai_response(user_message: str) -> str:
    return "Thanks for sharing. I’m here with you — tell me more."


def generate_ai_response(user_text: str, history=None) -> tuple[str, str]:
    """
    Returns (ai_text, model_name)
    """
    engine = get_engine()
    mode = engine.get("mode")
    print("ENGINE MODE:", mode)
    print("USER TEXT:", user_text)

    if mode == "brain":
        brain = engine["brain"]
        try:
            try:
                ai_text = brain.respond(user_text, history=history)
            except TypeError:
                ai_text = brain.respond(user_text)

            return ai_text, "aither-brain"
        except Exception as e:
            print("⚠️ brain.respond failed:", repr(e))
            return fallback_ai_response(user_text), "fallback"

    if mode == "loader":
        models = engine.get("models")

        if not isinstance(models, dict):
            print("⚠️ loader returned non-dict:", type(models))
            return fallback_ai_response(user_text), "fallback"

        safety = models.get("safety")
        if safety is not None:
            try:
                ok, _reason = safety.check(user_text)
                if not ok:
                    return "I can’t help with that.", "safety-block"
            except Exception as e:
                print("⚠️ safety.check failed:", repr(e))

        rag = models.get("rag")
        if rag is None:
            print("⚠️ loader models has no 'rag' (or it's None). Keys:", list(models.keys()))
            return fallback_ai_response(user_text), "fallback"

        try:
            if history is not None:
                ai_text = rag.generate(user_text, history=history)
            else:
                ai_text = rag.generate(user_text)

            return ai_text, "aither-model"

        except TypeError:
            try:
                ai_text = rag.generate(user_text)
                return ai_text, "aither-model"
            except Exception as e:
                print("⚠️ rag.generate failed:", repr(e))
                return fallback_ai_response(user_text), "fallback"

        except Exception as e:
            print("⚠️ rag.generate failed:", repr(e))
            return fallback_ai_response(user_text), "fallback"

    print("⚠️ No valid engine mode, using fallback")
    return fallback_ai_response(user_text), "fallback"


class TherapySessionViewSet(viewsets.ModelViewSet):
    serializer_class = TherapySessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = (
            TherapySession.objects
            .filter(user=self.request.user)
            .order_by("-last_activity", "-created_at", "-id")
        )

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
        queryset = (
            ChatMessage.objects
            .filter(session__user=self.request.user)
            .order_by("timestamp", "id")
        )

        session_id = self.request.query_params.get("session")
        if session_id:
            queryset = queryset.filter(session__id=session_id)

        sender = self.request.query_params.get("sender")
        if sender:
            queryset = queryset.filter(sender=sender)

        return queryset

    def perform_create(self, serializer):
        session = serializer.validated_data["session"]

        if session.user != self.request.user:
            raise PermissionDenied("Not your session")

        self.user_message = serializer.save(sender="user")

        history_qs = (
            ChatMessage.objects
            .filter(session=session)
            .order_by("-timestamp", "-id")
            .values("sender", "message")[:10]
        )
        history = list(history_qs)[::-1]

        start = time.time()
        try:
            ai_text, model_name = generate_ai_response(
                self.user_message.message,
                history=history
            )
        except Exception as e:
            print("⚠️ generate_ai_response failed:", repr(e))
            ai_text = fallback_ai_response(self.user_message.message)
            model_name = "fallback"

        latency_ms = int((time.time() - start) * 1000)

        self.ai_message = ChatMessage.objects.create(
            session=session,
            sender="ai",
            message=ai_text
        )

        session.last_activity = timezone.now()
        if session.message_count is None:
            session.message_count = 0
        session.message_count += 2
        session.save(update_fields=["last_activity", "message_count"])

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
                "session": TherapySessionSerializer(self.user_message.session).data,
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