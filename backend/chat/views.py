import time
import requests
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


# ----------------------------
# ML Engine (load once per process)
# ----------------------------

@lru_cache(maxsize=1)
def get_engine():
    """
    Load the ML engine once per Django process.

    Prefer loader (real model integration). Fall back to AitherBrain if present.
    """
    # Style 1: Loader-style model dict (recommended long term)
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

    # Style 2: Your current brain class (backward compatible)
    try:
        from ml.brain import AitherBrain
        brain = AitherBrain()
        print("✅ ML engine: AitherBrain loaded:", type(brain))
        return {"mode": "brain", "brain": brain}
    except Exception as e:
        print("⚠️ AitherBrain not available:", repr(e))

    # Nothing available
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

    if mode == "brain":
        brain = engine["brain"]
        try:
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

        # Optional safety check if your loader provides it
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

        # Try calling your model with history if supported
        try:
            if history is not None:
                ai_text = rag.generate(user_text, history=history)
            else:
                ai_text = rag.generate(user_text)
            return ai_text, "aither-model"

        except TypeError:
            # If rag.generate doesn't accept history, call without it
            try:
                ai_text = rag.generate(user_text)
                return ai_text, "aither-model"
            except Exception as e:
                print("⚠️ rag.generate failed:", repr(e))
                return fallback_ai_response(user_text), "fallback"

        except Exception as e:
            print("⚠️ rag.generate failed:", repr(e))
            return fallback_ai_response(user_text), "fallback"

    return fallback_ai_response(user_text), "fallback"


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

        # Build last ~10 messages as history (oldest -> newest)
        history_qs = (
            ChatMessage.objects
            .filter(session=session)
            .order_by("-timestamp")
            .values("sender", "message")[:10]
        )
        history = list(history_qs)[::-1]

        # Generate AI response
        start = time.time()
        try:
            ai_text, model_name = generate_ai_response(self.user_message.message, history=history)
        except Exception as e:
            print("⚠️ generate_ai_response failed:", repr(e))
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

#ADDED
MODEL_URL = "http://127.0.0.1:8001/analyze"  # your FastAPI

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    user = request.user
    session_id = request.data.get("session_id")
    message = request.data.get("message")

    session = TherapySession.objects.get(id=session_id, user=user)

    # 1. Save user message
    user_msg = ChatMessage.objects.create(
        session=session,
        sender="user",
        message=message
    )

    # 2. Call AI model
    start = time.time()
    res = requests.post(MODEL_URL, json={"text": message})
    latency = int((time.time() - start) * 1000)

    ai_data = res.json()
    ai_text = ai_data.get("response", "No response")

    # 3. Save AI response
    ai_msg = ChatMessage.objects.create(
        session=session,
        sender="ai",
        message=ai_text
    )

    # 4. Save AI interaction
    AIInteraction.objects.create(
        session=session,
        model_name="emotion-model",
        prompt=message,
        response=ai_text,
        latency_ms=latency
    )

    return Response({
        "user_message": user_msg.message,
        "ai_message": ai_msg.message,
        "latency_ms": latency
    })

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
