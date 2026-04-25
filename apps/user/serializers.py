# apps/users/serializers/register.py
from rest_framework import serializers
from .models import User, OtpLog
from .utils import (
    send_registration_otp_email,
    send_otp_email,
    send_forgot_password_otp_email
)
from apps.user.firebase import verify_firebase_token
from django.contrib.auth import authenticate
import logging

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    can_scan = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "profile_image",
            "profile_image_url",
            "subscription_type",
            "subscription_start_date",
            "subscription_end_date",
            "free_scans_remaining",
            "total_scans_used",
            "is_premium",
            "can_scan",
            'language_preference',
            'terms_and_conditions_accepted',
        ]
        read_only_fields = ['id', 'email', 'subscription_type', 'subscription_start_date',]


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

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "User with this email already exists"
            )
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                {"message": "Passwords do not match"}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            is_active=False,
            is_superuser=False,
            is_staff=False
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


# class LoginRequestOtpSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     password = serializers.CharField(write_only=True)

#     def validate(self, attrs):
#         email = attrs['email']
#         password = attrs['password']

#         try:
#             user = User.objects.get(email=email)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("Invalid credentials")

#         if not user.is_active:
#             raise serializers.ValidationError("Account not verified")

#         if not user.check_password(password):
#             raise serializers.ValidationError("Invalid credentials")

#         self.user = user
#         return attrs

#     def save(self):
#         # Send OTP email
#         send_login_otp_email(self.user)

#         # Return user so view can access email
#         return self.user


# class LoginVerifyOtpSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     otp = serializers.CharField(max_length=6)

#     def validate(self, attrs):
#         user = User.objects.filter(email=attrs['email'], is_active=True).first()
#         if not user:
#             raise serializers.ValidationError("Invalid user")

#         otp_obj = user.otp_logs.order_by('-created_at').first()

#         if not otp_obj or otp_obj.otp != attrs['otp']:
#             raise serializers.ValidationError("Invalid OTP")

#         if not otp_obj.otp_is_valid():
#             raise serializers.ValidationError("OTP expired")
#         tokens = get_tokens_for_user(user)
#         return (
#             {
#                 "user": UserSerializer(user).data,
#                 "tokens": tokens
#             }
#         )

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email = data.get('email', '').lower()
        password = data.get('password')
        
        if not email or not password:
            raise serializers.ValidationError("Email and password required")
        
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        
        if not user.is_active:
            raise serializers.ValidationError("Account disabled")
        
        data['user'] = user
        return data


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
        otp_log.generate_otp()
        # send otp
        send_otp_email(self.user)
        return otp_log


class FirebaseAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()

    def validate(self, attrs):
        id_token = attrs.get("id_token")
        
        logger.debug(f"Received Firebase token: {id_token[:50]}...")
        
        try:
            decoded = verify_firebase_token(id_token)
            logger.debug(f"Token decoded successfully: {decoded}")
        except Exception as e:
            logger.error(f"Firebase verification error: {type(e).__name__} - {str(e)}", exc_info=True)
            raise serializers.ValidationError({"firebase_error": str(e)})

        email = decoded.get("email")
        name = decoded.get("name", "")
        picture = decoded.get("picture")

        # Split name safely
        name_parts = name.split(" ")
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        # Create or Get User
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
                "is_superuser": False,
                "is_staff": False,
            }
        )

        # Update profile image if it's new
        if (
            picture
            and hasattr(user, "profile_image_url")
            and not user.profile_image_url
        ):
            user.profile_image_url = picture
            user.save()

        # Generate your internal JWT tokens (SimpleJWT example)
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)

        return {
            "user": {
                "email": user.email,
                "first_name": user.first_name,
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }


class ForgotPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            self.user = User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        return value

    def save(self):
        otp_log = OtpLog.objects.create(user=self.user)
        otp = otp_log.generate_otp()

        send_forgot_password_otp_email(self.user)

        return {"message": "OTP sent successfully"}


class ForgotPasswordVerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = attrs["email"]
        otp = attrs["otp"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email.")

        otp_log = (
            OtpLog.objects
            .filter(user=user, otp=otp)
            .order_by("-created_at")
            .first()
        )

        if not otp_log:
            raise serializers.ValidationError("Invalid OTP.")

        if not otp_log.otp_is_valid():
            raise serializers.ValidationError("OTP expired.")

        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(
        min_length=8,
        write_only=True
    )
    confirm_password = serializers.CharField(
        min_length=8,
        write_only=True
    )

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        try:
            self.user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email.")

        otp_log = (
            OtpLog.objects
            .filter(user=self.user, otp=otp)
            .order_by("-created_at")
            .first()
        )

        if not otp_log:
            raise serializers.ValidationError("Invalid OTP.")

        if not otp_log.otp_is_valid():
            raise serializers.ValidationError("OTP expired.")

        return attrs

    def save(self):
        self.user.set_password(self.validated_data["new_password"])
        self.user.save(update_fields=["password"])

        OtpLog.objects.filter(user=self.user).delete()

        return {
            "message": "Password reset successful"
        }
    

class LanguagePreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['language_preference']


class TermsAndConditionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['terms_and_conditions_accepted']