from django.urls import path

from .views import RegisterView, LoginView, ReferralCodeView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('referral_code/', ReferralCodeView.as_view(), name='referral_code'),
]
