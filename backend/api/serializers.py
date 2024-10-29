from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from referral_system.models import ReferralCode, ReferralRelationship


User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя."""

    password = serializers.CharField(
        min_length=8, max_length=128, write_only=True
    )
    referral_code = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'referral_code')

    def create(self, validated_data):
        referral_code = validated_data.pop('referral_code', None)
        user = User.objects.create_user(**validated_data)

        if referral_code:
            referral_code_obj = get_object_or_404(
                ReferralCode, code=referral_code
            )

            if referral_code_obj.is_expired():
                raise serializers.ValidationError(
                    {'referral_code': 'Срок действия реферального кода истек.'}
                )

            ReferralRelationship.objects.create(
                referrer=referral_code_obj.user,
                referral=user
            )

        return user


class LoginSerializer(serializers.Serializer):
    """Сериализатор для аутентификации пользователя."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    class Meta:
        fields = ('username', 'password')

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        if username and password:
            user = User.objects.get(username=username)
            if user and user.check_password(password):
                data['user'] = user
                return data
            else:
                raise serializers.ValidationError(
                    'Неверные имя пользователя или пароль.'
                )
        else:
            raise serializers.ValidationError(
                'Необходимо ввести имя пользователя и пароль.'
            )


class ReferralCodeSerializer(serializers.ModelSerializer):
    """Сериализатор для реферального кода."""

    class Meta:
        model = ReferralCode
        fields = ('code', 'expiration_date')


class EmailSerializer(serializers.Serializer):
    """Сериализатор для получения реферального кода по email."""

    email = serializers.EmailField()


class ReferralSerializer(serializers.ModelSerializer):
    referral_username = serializers.CharField(
        source='referral.username', read_only=True
    )
    referral_email = serializers.EmailField(
        source='referral.email', read_only=True
    )

    class Meta:
        model = ReferralRelationship
        fields = ('referral_username', 'referral_email')
