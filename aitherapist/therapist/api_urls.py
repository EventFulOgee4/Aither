from django.urls import path
from .views import (
    HealthView, MeView,
    ChatSessionListCreateView, ChatSessionMessagesView, ChatMessageView,
    MoodListCreateView, MoodStatsView
)

urlpatterns = [
    path("health/", HealthView.as_view()),
    path("me/", MeView.as_view()),

    # chat
    path("chat/sessions/", ChatSessionListCreateView.as_view()),
    path("chat/sessions/<int:session_id>/messages/", ChatSessionMessagesView.as_view()),
    path("chat/message/", ChatMessageView.as_view()),

    # mood
    path("mood/", MoodListCreateView.as_view()),
    path("mood/stats/", MoodStatsView.as_view()),
]