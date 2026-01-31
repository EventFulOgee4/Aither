from django.shortcuts import render

# Create your views here.

from rest_framework import generics, permissions, decorators, response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import RegisterSerializer
import uuid
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user
    return Response({
        "username": user.username,
        "email": user.email
    })

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def guest_login(request):
    # 1. Create unique guest username
    username = f"guest_{uuid.uuid4().hex[:10]}"

    # 2. Create user with no password
    user = User.objects.create_user(
        username=username,
        password=None
    )
    user.set_unusable_password()
    user.save()

    # 3. Issue JWT tokens
    refresh = RefreshToken.for_user(user)

    return Response({
        "guest": True,
        "username": user.username,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    })