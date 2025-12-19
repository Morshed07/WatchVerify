from django.urls import path
from .views import (
    RegisterView,
    VerifyRegisterOtpView,
    LoginRequestOtpView,
    LoginVerifyOtpView,
    ResendOtpView,
    GoogleAuthView,
)

urlpatterns = [
    path('user/register/', RegisterView.as_view(), name='register'),
    path('user/register/verify/', VerifyRegisterOtpView.as_view()),

    path('user/login/', LoginRequestOtpView.as_view()),
    path('user/login/verify/', LoginVerifyOtpView.as_view()),

    path('user/otp/resend/', ResendOtpView.as_view()),

    path('user/google-auth/', GoogleAuthView.as_view()),
]
