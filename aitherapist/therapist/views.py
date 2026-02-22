from datetime import timedelta
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from .models import ChatSession, ChatMessage, MoodEntry
from .serializers import ChatSessionSerializer, ChatMessageSerializer, MoodEntrySerializer


def stub_ai_reply(user_text: str) -> dict:
    # Later: replace with your PyTorch model call
    return {
        "reply": f"I hear you. Tell me more about that: {user_text}",
        "emotion": "calm",
        "confidence": 0.7,
        "avatar_state": "idle",
    }


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok", "service": "aither-backend"})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response({"username": u.username, "email": u.email})


# -------- CHAT --------

class ChatSessionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = ChatSession.objects.filter(user=request.user)
        return Response(ChatSessionSerializer(sessions, many=True).data)

    def post(self, request):
        title = (request.data.get("title") or "New Session").strip()
        session = ChatSession.objects.create(user=request.user, title=title)
        return Response(ChatSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class ChatSessionMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id: int):
        session = ChatSession.objects.filter(id=session_id, user=request.user).first()
        if not session:
            return Response({"detail": "session not found"}, status=status.HTTP_404_NOT_FOUND)

        msgs = ChatMessage.objects.filter(session=session)
        return Response(ChatMessageSerializer(msgs, many=True).data)


class ChatMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = (request.data.get("message") or "").strip()
        if not text:
            return Response({"detail": "message is required"}, status=status.HTTP_400_BAD_REQUEST)

        session_id = request.data.get("session_id")

        if session_id:
            session = ChatSession.objects.filter(id=session_id, user=request.user).first()
            if not session:
                return Response({"detail": "session not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            session = ChatSession.objects.create(user=request.user, title="New Session")

        user_msg = ChatMessage.objects.create(session=session, role="user", content=text)

        ai = stub_ai_reply(text)

        assistant_msg = ChatMessage.objects.create(
            session=session,
            role="assistant",
            content=ai["reply"],
            emotion=ai["emotion"],
            confidence=ai["confidence"],
            avatar_state=ai["avatar_state"],
        )

        return Response({
            "session": ChatSessionSerializer(session).data,
            "user_message": ChatMessageSerializer(user_msg).data,
            "assistant_message": ChatMessageSerializer(assistant_msg).data,
        })


# -------- MOOD --------

class MoodListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = MoodEntry.objects.filter(user=request.user)
        return Response(MoodEntrySerializer(qs, many=True).data)

    def post(self, request):
        ser = MoodEntrySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        entry = MoodEntry.objects.create(user=request.user, **ser.validated_data)
        return Response(MoodEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class MoodStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        since = timezone.now() - timedelta(days=30)
        qs = MoodEntry.objects.filter(user=request.user, created_at__gte=since)

        counts = {key: qs.filter(mood=key).count() for key, _ in MoodEntry.MOOD_CHOICES}
        return Response({"window_days": 30, "counts": counts})