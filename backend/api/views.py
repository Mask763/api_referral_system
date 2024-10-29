import asyncio

from django.contrib.auth import authenticate
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserRegistrationSerializer, LoginSerializer


class RegisterView(APIView):
    """Регистрация нового пользователя."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {f'Пользователь {user.username} успешно создан.'},
            status=status.HTTP_201_CREATED
        )

    async def async_post(self, request):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.post, request)
        return result


class LoginView(APIView):
    """Аутентификация пользователя."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        return Response(
            {'detail': 'Неверные учетные данные'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    async def async_post(self, request):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.post, request)
        return result
