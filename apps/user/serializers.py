# apps/users/serializers/register.py
from rest_framework import serializers
from .models import User, OtpLog
from .utils import (
    send_registration_otp_email,
    send_login_otp_email,
    send_password_reset_email,
    send_otp_email,
    get_tokens_for_user
)
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from google.auth.transport import requests as google_requests


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'profile_image')
        read_only_fields = ('id',)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
            'password',
            'confirm_password',
        )

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            is_active=False,
        )

        send_registration_otp_email(user)
        return user


class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        otp_obj = user.otp_logs.order_by('-created_at').first()

        if not otp_obj or otp_obj.otp != attrs['otp']:
            raise serializers.ValidationError("Invalid OTP")

        if not otp_obj.otp_is_valid():
            raise serializers.ValidationError("OTP expired")

        user.is_active = True
        user.save(update_fields=['is_active'])

        # tokens = get_tokens_for_user(user)
        # return {
        #     "user": user,
        #     "tokens": tokens
        # }
        return attrs


class LoginRequestOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs['email']
        password = attrs['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_active:
            raise serializers.ValidationError("Account not verified")

        # ✅ Validate password
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")

        self.user = user
        return attrs

    def save(self):
        # ✅ Send OTP only after password validation
        send_login_otp_email(self.user)

        return {
            "message": "OTP sent successfully"
        }


class LoginVerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        user = User.objects.filter(email=attrs['email'], is_active=True).first()
        if not user:
            raise serializers.ValidationError("Invalid user")

        otp_obj = user.otp_logs.order_by('-created_at').first()

        if not otp_obj or otp_obj.otp != attrs['otp']:
            raise serializers.ValidationError("Invalid OTP")

        if not otp_obj.otp_is_valid():
            raise serializers.ValidationError("OTP expired")
        tokens = get_tokens_for_user(user)
        return (
            {
                "user": UserSerializer(user).data,
                "tokens": tokens
            }
        )


class ResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        self.user = User.objects.filter(email=attrs['email']).first()
        if not self.user:
            raise serializers.ValidationError("User not found")

        last_otp = self.user.otp_logs.order_by('-created_at').first()
        if last_otp and not last_otp.can_resend():
            raise serializers.ValidationError("Please wait before resending OTP")
        return attrs

    def save(self):
        otp_obj = OtpLog.objects.create(user=self.user)
        otp = otp_obj.generate_otp()
        # send otp
        send_otp_email(self.user)
        return otp


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()

    def validate(self, attrs):
        try:
            # 1. Verify the token with Google
            payload = id_token.verify_oauth2_token(
                attrs['id_token'],
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
        except Exception:
            raise serializers.ValidationError("Invalid Google token")

        # 2. Extract user info from Google payload
        email = payload.get("email")
        name = payload.get("name", "")
        picture_url = payload.get("picture")  # Google returns this URL

        # 3. Get or Create user
        # We use email as the unique identifier
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": name.split(" ")[0] if name else "",
                "last_name": " ".join(name.split(" ")[1:]) if name else "",
            }
        )

        user.profile_image_url = picture_url
        user.save()

        # 5. Generate your backend tokens (using your helper function)
        tokens = get_tokens_for_user(user)

        return {
            "user": user,
            "tokens": tokens
        }