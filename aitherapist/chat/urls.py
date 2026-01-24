from django.urls import path
from .views import test_api
from .views import TherapySessionViewSet, ChatMessageViewSet

urlpatterns = [
    path('sessions/', TherapySessionViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('messages/', ChatMessageViewSet.as_view({'get': 'list', 'post': 'create'})),
]

urlpatterns = [
    path('test/', test_api),
]