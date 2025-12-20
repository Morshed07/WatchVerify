from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from .models import User, OtpLog
from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def send_registration_otp_email(user: User):
    otp_obj = OtpLog.objects.create(user=user)
    otp_code = otp_obj.generate_otp()
    html_message = render_to_string(
        'email/otp_email.html',
        {'otp': otp_code, 'user': user}
    )

    email = EmailMessage(
        subject='Your One-Time Password for Registration',
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email]
    )
    email.content_subtype = 'html'
    return email.send()


def send_otp_email(user: User):
    otp_obj = OtpLog.objects.create(user=user)
    otp_code = otp_obj.generate_otp()
    html_message = render_to_string(
        'email/otp_email.html',
        {'otp': otp_code, 'user': user}
    )

    email = EmailMessage(
        subject='Your One-Time Password',
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email]
    )
    email.content_subtype = 'html'
    return email.send()


def send_login_otp_email(user: User):
    otp_obj = OtpLog.objects.create(user=user)
    otp_code = otp_obj.generate_otp()
    html_message = render_to_string(
        'email/otp_email.html',
        {'otp': otp_code, 'user': user}
    )

    email = EmailMessage(
        subject='Your One-Time Password for Login',
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email]
    )
    email.content_subtype = 'html'
    return email.send()


def send_forgot_password_otp_email(user: User):
    otp_obj = OtpLog.objects.create(user=user)
    otp_code = otp_obj.generate_otp()
    html_message = render_to_string(
        'email/otp_email.html',
        {'otp': otp_code, 'user': user}
    )

    email = EmailMessage(
        subject='You requested a password reset OTP',
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email]
    )
    email.content_subtype = 'html'
    return email.send()
