from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()
MAX_LENGTH_REFERRAL_CODE = 20


class ReferralCode(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='referral_code'
    )
    code = models.CharField(
        max_length=MAX_LENGTH_REFERRAL_CODE, unique=True
    )
    expiration_date = models.DateTimeField()

    def is_expired(self):
        return self.expiration_date < timezone.now()
