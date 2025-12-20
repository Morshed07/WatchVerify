from django.urls import path
from .views import (
    RegisterView,
    VerifyRegisterOtpView,
    LoginRequestOtpView,
    LoginVerifyOtpView,
    ResendOtpView,
    FirebaseAuthView,
    ForgotPasswordView,
    ForgotPasswordVerifyOtpView,
    ResetPasswordView,
    UserMeView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('user/register/', RegisterView.as_view(), name='register'),
    path('user/register/verify/', VerifyRegisterOtpView.as_view(), name='verify-register-otp'),

    path('user/login/', LoginRequestOtpView.as_view(), name='login-request-otp'),
    path('user/login/verify/', LoginVerifyOtpView.as_view(), name='login-verify-otp'),

    path('user/otp/resend/', ResendOtpView.as_view(), name='resend-otp'),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('user/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('user/forgot-password-otp/verify/', ForgotPasswordVerifyOtpView.as_view(), name='verify-forgot-password-otp'),
    path('user/reset-password/', ResetPasswordView.as_view(), name='reset-password'),

    path('user/me/', UserMeView.as_view(), name='user-me'),


    path('user/firebase-auth/', FirebaseAuthView.as_view(), name='firebase-auth'),
]
