import asyncio
import uuid

from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserRegistrationSerializer, LoginSerializer, ReferralCodeSerializer
from referral_system.models import ReferralCode, MAX_LENGTH_REFERRAL_CODE


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


class ReferralCodeView(APIView):
    """Получение/удаление реферального кода."""

    def post(self, request):
        user = request.user

        if (hasattr(user, 'referral_code') and not
           user.referral_code.is_expired()):
            return Response(
                {'detail': 'У вас уже есть активный реферальный код.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        code = str(uuid.uuid4())[:MAX_LENGTH_REFERRAL_CODE]
        expiration_date = timezone.now() + timezone.timedelta(days=7)
        referral_code = ReferralCode.objects.create(
            user=user,
            code=code,
            expiration_date=expiration_date
        )
        serializer = ReferralCodeSerializer(referral_code)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    async def async_post(self, request):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.post, request)
        return result

    def delete(self, request):
        user = request.user

        if not hasattr(user, 'referral_code'):
            return Response(
                {'detail': 'У вас нет активного реферального кода.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.referral_code.delete()
        return Response(
            {'detail': 'Реферальный код успешно удален.'},
            status=status.HTTP_204_NO_CONTENT
        )

    async def async_delete(self, request):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.delete, request)
        return result
