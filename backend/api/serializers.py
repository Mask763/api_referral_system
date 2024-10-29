from django.contrib.auth import get_user_model
from rest_framework import serializers, validators


User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя."""

    password = serializers.CharField(
        min_length=8, max_length=128, write_only=True
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
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
