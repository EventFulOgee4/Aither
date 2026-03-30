import time
import json
from functools import lru_cache

from django.utils import timezone
from django.db.models import Avg, Min, Max
from django.db.models.functions import Length
from django.http import StreamingHttpResponse

from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied

from .models import TherapySession, ChatMessage, MoodEntry, AIInteraction
from .serializers import TherapySessionSerializer, ChatMessageSerializer, MoodEntrySerializer


@lru_cache(maxsize=1)
def get_engine():
    try:
        from ml.loader import get_model
        models = get_model()
        print("✅ ML engine: loader loaded. Keys:", list(models.keys()))
        return {"mode": "loader", "models": models}
    except Exception as e:
        print("⚠️ ml.loader.get_model not available:", repr(e))

    try:
        from ml.brain import AitherBrain
        brain = AitherBrain()
        print("✅ ML engine: AitherBrain loaded")
        return {"mode": "brain", "brain": brain}
    except Exception as e:
        print("⚠️ AitherBrain not available:", repr(e))

    print("❌ ML engine: none (will use fallback)")
    return {"mode": "none"}


def get_brain():
    """Get the AitherBrain instance from whichever engine is loaded."""
    engine = get_engine()
    mode = engine.get("mode")
    if mode == "brain":
        return engine["brain"]
    if mode == "loader":
        models = engine.get("models", {})
        rag = models.get("rag")
        # BrainRagAdapter wraps the brain — get it directly
        if hasattr(rag, "brain"):
            return rag.brain
    return None


def fallback_ai_response(user_message: str) -> str:
    return "Thanks for sharing. I'm here with you — tell me more."


def generate_ai_response(user_text: str, history=None) -> tuple[str, str]:
    engine = get_engine()
    mode = engine.get("mode")
    print("ENGINE MODE:", mode)
    print("USER TEXT:", user_text)

    if mode == "brain":
        brain = engine["brain"]
        try:
            return brain.respond(user_text, history=history), "aither-brain"
        except Exception as e:
            print("⚠️ brain.respond failed:", repr(e))
            return fallback_ai_response(user_text), "fallback"

    if mode == "loader":
        models = engine.get("models", {})
        rag = models.get("rag")
        if rag is None:
            return fallback_ai_response(user_text), "fallback"
        try:
            ai_text = rag.generate(user_text, history=history)
            return ai_text, "aither-model"
        except TypeError:
            try:
                return rag.generate(user_text), "aither-model"
            except Exception as e:
                print("⚠️ rag.generate failed:", repr(e))
                return fallback_ai_response(user_text), "fallback"
        except Exception as e:
            print("⚠️ rag.generate failed:", repr(e))
            return fallback_ai_response(user_text), "fallback"

    return fallback_ai_response(user_text), "fallback"


def maybe_generate_title(session, user_message: str):
    """
    If the session still has the default title and this is the first message,
    generate a meaningful title using the brain.
    """
    if session.title not in ("New Session", "", None):
        return  # Already has a real title

    message_count = ChatMessage.objects.filter(session=session).count()
    if message_count > 1:
        return  # Not the first message

    brain = get_brain()
    if brain and hasattr(brain, "generate_session_title"):
        try:
            title = brain.generate_session_title(user_message)
            if title and title != "New Session":
                session.title = title
                session.save(update_fields=["title"])
                print(f"✅ Session title set: '{title}'")
        except Exception as e:
            print("⚠️ Title generation failed:", repr(e))


# ── Streaming endpoint ─────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def stream_message(request):
    """
    POST /api/chat/stream/
    Body: { "session": <id>, "message": "<text>" }

    Returns a streaming SSE response where each chunk is:
      data: <text chunk>\n\n

    Final chunk:
      data: [DONE]\n\n
    """
    session_id = request.data.get("session")
    user_text = (request.data.get("message") or "").strip()

    if not user_text:
        return Response({"error": "message is required"}, status=400)

    # Get or create session
    if session_id:
        try:
            session = TherapySession.objects.get(id=session_id, user=request.user)
        except TherapySession.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)
    else:
        session = TherapySession.objects.create(
            user=request.user,
            title="New Session"
        )

    # Save user message
    user_message = ChatMessage.objects.create(
        session=session,
        sender="user",
        message=user_text,
    )

    # Get history
    history_qs = (
        ChatMessage.objects
        .filter(session=session)
        .order_by("-timestamp", "-id")
        .values("sender", "message")[:10]
    )
    history = list(history_qs)[::-1]

    # Generate title on first message
    maybe_generate_title(session, user_text)

    # Get brain for streaming
    brain = get_brain()

    def event_stream():
        full_response = []

        # Send session + user message info first as metadata
        meta = {
            "type": "meta",
            "session_id": session.id,
            "session_title": session.title,
            "user_message_id": user_message.id,
        }
        yield f"data: {json.dumps(meta)}\n\n"

        if brain and hasattr(brain, "respond_stream"):
            for chunk in brain.respond_stream(user_text, history=history):
                full_response.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
        else:
            # Fallback — send full response as single chunk
            text, _ = generate_ai_response(user_text, history=history)
            full_response.append(text)
            yield f"data: {json.dumps({'type': 'chunk', 'text': text})}\n\n"

        # Save the complete AI response
        ai_text = "".join(full_response)
        ai_message = ChatMessage.objects.create(
            session=session,
            sender="ai",
            message=ai_text,
        )

        session.last_activity = timezone.now()
        if session.message_count is None:
            session.message_count = 0
        session.message_count += 2
        session.save(update_fields=["last_activity", "message_count", "title"])

        # Send final message with AI message ID
        done_meta = {
            "type": "done",
            "ai_message_id": ai_message.id,
        }
        yield f"data: {json.dumps(done_meta)}\n\n"

    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


# ── Standard viewsets ──────────────────────────────────────────────────────

class TherapySessionViewSet(viewsets.ModelViewSet):
    serializer_class = TherapySessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            TherapySession.objects
            .filter(user=self.request.user)
            .order_by("-last_activity", "-created_at", "-id")
        )

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

        # Auto-title on first message
        maybe_generate_title(session, self.user_message.message)

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
        session.save(update_fields=["last_activity", "message_count", "title"])

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
    try:
        session = TherapySession.objects.get(id=session_id, user=request.user)
    except TherapySession.DoesNotExist:
        return Response({"detail": "Session not found or not yours"}, status=404)

    messages = session.messages.all()
    moods = session.moods.all()

    return Response({
        "session_id": session.id,
        "title": session.title,
        "created_at": session.created_at,
        "user_messages": messages.filter(sender="user").count(),
        "ai_messages": messages.filter(sender="ai").count(),
        "last_activity": messages.last().timestamp if messages.exists() else None,
        "average_message_length": messages.aggregate(avg_len=Avg(Length("message")))["avg_len"] if messages.exists() else None,
        "mood_count": moods.count(),
        "average_mood": moods.aggregate(avg=Avg("intensity"))["avg"] if moods.exists() else None,
        "min_mood_intensity": moods.aggregate(min=Min("intensity"))["min"] if moods.exists() else None,
        "max_mood_intensity": moods.aggregate(max=Max("intensity"))["max"] if moods.exists() else None,
        "session_duration_seconds": (
            (messages.last().timestamp - session.created_at).total_seconds()
            if messages.exists() else 0
        ),
    })