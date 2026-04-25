from django.urls import path
from .views import (
    RegisterView,
    VerifyRegisterOtpView,
    # LoginRequestOtpView,
    # LoginVerifyOtpView,
    ResendOtpView,
    FirebaseAuthView,
    FirebaseTokenDebugView,
    ForgotPasswordView,
    ForgotPasswordVerifyOtpView,
    ResetPasswordView,
    UserMeView,
    LanguagePreferenceView,
    LoginAPIView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('user/register/', RegisterView.as_view(), name='register'),
    path('user/register/verify/', VerifyRegisterOtpView.as_view(), name='verify-register-otp'),

    path('user/login/', LoginAPIView.as_view(), name='login'),
    # path('user/login/verify/', LoginVerifyOtpView.as_view(), name='login-verify-otp'),

    path('user/otp/resend/', ResendOtpView.as_view(), name='resend-otp'),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('user/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('user/forgot-password-otp/verify/', ForgotPasswordVerifyOtpView.as_view(), name='verify-forgot-password-otp'),
    path('user/reset-password/', ResetPasswordView.as_view(), name='reset-password'),

    path('user/me/', UserMeView.as_view(), name='user-me'),
    path('user/firebase-auth/', FirebaseAuthView.as_view(), name='firebase-auth'),
    path('user/firebase-token-debug/', FirebaseTokenDebugView.as_view(), name='firebase-token-debug'),
    
    path('user/language-preference/', LanguagePreferenceView.as_view(), name='language-preference'),


]
