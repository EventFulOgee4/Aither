from django.urls import path
from .views import ChatMessageViewSet

urlpatterns = [
    path('messages/', ChatMessageViewSet.as_view({'get': 'list', 'post': 'create'}), name='chat-messages'),
]   