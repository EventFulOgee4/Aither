from django.urls import path
from .views import (
    test_api,
    TherapySessionViewSet,
    ChatMessageViewSet,
    MoodEntryViewSet,
    session_metadata,
    send_message
)

urlpatterns = [
    path('test/', test_api),

    # Sessions
    path(
        'sessions/',
        TherapySessionViewSet.as_view({
            'get': 'list',
            'post': 'create'
        })
    ),

    # 🔥 THIS IS THE IMPORTANT NEW ROUTE
    path(
        'sessions/<int:pk>/',
        TherapySessionViewSet.as_view({
            'delete': 'destroy'
        })
    ),

    # Messages
    path(
        'messages/',
        ChatMessageViewSet.as_view({
            'get': 'list',
            'post': 'create'
        })
    ),

    # Moods
    path(
        'moods/',
        MoodEntryViewSet.as_view({
            'get': 'list',
            'post': 'create'
        })
    ),

    # Session analytics
    path(
        'sessions/<int:session_id>/metadata/',
        session_metadata,
        name='session-metadata'
    ),
]
