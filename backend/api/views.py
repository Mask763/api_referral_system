import asyncio
import uuid

from django.core.cache import cache
from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .constants import TIME_TO_CACHE
from .serializers import (
    UserRegistrationSerializer, LoginSerializer,
    ReferralCodeSerializer, EmailSerializer,
    ReferralSerializer
)
from referral_system.constants import MAX_LENGTH_REFERRAL_CODE
from referral_system.models import ReferralCode


User = get_user_model()


class RegisterView(APIView):
    """Регистрация нового пользователя."""

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
            request_body=UserRegistrationSerializer,
            responses={201: openapi.Response(
                'Регистрация пользователя',
                openapi.Schema(type=openapi.TYPE_STRING)
            )}
        )
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

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                'Аутентификация пользователя', LoginSerializer
            ),
            401: openapi.Response(
                'Неверные учетные данные',
                openapi.Schema(type=openapi.TYPE_STRING)
            )
        }
    )
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
    """Создание/удаление реферального кода."""

    @swagger_auto_schema(
            responses={
                201: openapi.Response(
                    'Создание реферального кода', ReferralCodeSerializer
                ),
                400: openapi.Response(
                    'У вас уже есть активный реферальный код.',
                    openapi.Schema(type=openapi.TYPE_STRING)
                )
            }
    )
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

        # Добавляем реферальный код в кеш на 1 день
        cache_key = f'referral_code_{user.email}'
        cache.set(cache_key, referral_code, timeout=TIME_TO_CACHE)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    async def async_post(self, request):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.post, request)
        return result

    @swagger_auto_schema(
        responses={
            204: openapi.Response(
                'Удаление реферального кода'
            ),
            400: openapi.Response(
                'У пользователя нет активного реферального кода',
                openapi.Schema(type=openapi.TYPE_STRING)
            )
        }
    )
    def delete(self, request):
        user = request.user

        if not hasattr(user, 'referral_code'):
            return Response(
                {'detail': 'У вас нет активного реферального кода.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Очищаем кеш для реферального кода пользователя
        cache_key = f'referral_code_{user.email}'
        cache.delete(cache_key)

        user.referral_code.delete()
        return Response(
            {'detail': 'Реферальный код успешно удален.'},
            status=status.HTTP_204_NO_CONTENT
        )

    async def async_delete(self, request):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.delete, request)
        return result


class GetReferralCodeByEmailView(APIView):
    """Получение реферального кода по email реферера."""

    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(
        request_body=EmailSerializer,
        responses={
            200: openapi.Response(
                'Получение реферального кода по email реферера',
                ReferralCodeSerializer
            ),
            404: openapi.Response(
                'У пользователя нет активного реферального кода',
                openapi.Schema(type=openapi.TYPE_STRING)
            ),
            400: openapi.Response(
                'Срок действия реферального кода истек',
                openapi.Schema(type=openapi.TYPE_STRING)
            )
        }
    )
    def post(self, request):
        email_serializer = EmailSerializer(data=request.data)
        email_serializer.is_valid(raise_exception=True)
        email = email_serializer.validated_data.get('email')
        referrer = get_object_or_404(User, email=email)

        # Проверяем, есть ли реферальный код в кеше
        cache_key = f'referral_code_{email}'
        referral_code = cache.get(cache_key)

        try:
            referral_code = referrer.referral_code
            # Кешируем реферальный код на 1 день
            cache.set(cache_key, referral_code, timeout=TIME_TO_CACHE)
        except ReferralCode.DoesNotExist:
            return Response(
                {'detail': 'У этого пользователя нет активного кода.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if referral_code.is_expired():
            return Response(
                {'detail': 'Срок действия реферального кода истек.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ReferralCodeSerializer(referral_code)
        return Response(serializer.data)

    async def async_get(self, request, email):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.get, request, email)
        return result


class ReferralsListView(APIView):
    """Получение списка рефералов."""

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                'Получение списка рефералов',
                ReferralSerializer
            ),
            404: openapi.Response(
                'У пользователя нет рефералов',
                openapi.Schema(type=openapi.TYPE_STRING)
            )
        }
    )    
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        referrals = user.referrals.all()

        if not referrals:
            return Response(
                {'detail': 'У этого пользователя нет рефералов.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ReferralSerializer(referrals, many=True)
        return Response(serializer.data)

    async def async_get(self, request, referrer_id):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, self.get, request, referrer_id
        )
        return result
