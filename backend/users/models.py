from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import MAX_CHARFIELD_LENGTH, MAX_EMAIL_LENGTH


class ApplicationUser(AbstractUser):
    """Модель пользователя."""

    REQUIRED_FIELDS = (
        'email',
    )

    username = models.CharField(
        max_length=MAX_CHARFIELD_LENGTH,
        unique=True,
        validators=[AbstractUser.username_validator],
        error_messages={
            'unique': "Пользователь с таким именем уже существует.",
        },
        verbose_name='Имя пользователя'
    )
    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким email уже существует.'
        },
        verbose_name='Email',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username
