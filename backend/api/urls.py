from django.urls import path

from .views import (
    RegisterView, LoginView, ReferralCodeView,
    GetReferralCodeByEmailView, ReferralsListView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('referral_code/', ReferralCodeView.as_view(), name='referral_code'),
    path(
        'referral_code/get_by_email/',
        GetReferralCodeByEmailView.as_view(),
        name='get_referral_code_by_email'
    ),
    path(
        'referrals/<int:pk>/',
        ReferralsListView.as_view(),
        name='referrals'
    ),
]
