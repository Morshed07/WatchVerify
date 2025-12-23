from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.utils import timezone
from datetime import timedelta
import random
from apps.core.models import BaseModel


def user_image_upload_path(instance, filename):
    user_email = instance.email.replace("@", "_")
    return f"{user_email}/profile_image/{filename}"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError("Users must have an email address")    
        email = self.normalize_email(email).lower()

        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **kwargs):
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)

        if kwargs["is_staff"] is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if kwargs["is_superuser"] is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **kwargs)


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    SUBSCRIPTION_TYPES = [
        ('free', 'Free'),
        ('pay_per_scan', 'Pay Per Scan'),
        ('premium', 'Premium'),
        ('unlimited', 'Unlimited'),
    ]
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )
    last_name = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )
    subscription_type = models.CharField(
        max_length=20, 
        choices=SUBSCRIPTION_TYPES,
        default='free'
    )
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    free_scans_remaining = models.IntegerField(default=3)
    total_scans_used = models.IntegerField(default=0)
    is_premium = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=True)

    profile_image = models.ImageField(
        upload_to=user_image_upload_path,
        null=True,
        blank=True
    )
    profile_image_url = models.URLField(
        max_length=500,
        null=True,
        blank=True
    )
    objects = UserManager()
    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

        db_table = 'users'
        indexes = [
            models.Index(fields=['subscription_type', 'subscription_end_date']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return self.email or f'{self.first_name} {self.last_name}'.strip()
    
    @property
    def is_subscription_active(self):
        if self.subscription_type == 'free':
            return self.free_scans_remaining > 0
        
        if self.subscription_end_date:
            return timezone.now() <= self.subscription_end_date
        return False
    
    @property
    def can_scan(self):
        if self.subscription_type == 'free':
            return self.free_scans_remaining > 0
        elif self.subscription_type == 'unlimited':
            return self.is_subscription_active
        else:
            return self.is_subscription_active
    
    def decrement_free_scans(self):
        if self.subscription_type == 'free' and self.free_scans_remaining > 0:
            self.free_scans_remaining -= 1
            self.save(update_fields=['free_scans_remaining'])


class OtpLog(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='otp_logs'
    )
    otp = models.CharField(max_length=6)

    resend_after = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def generate_otp(self, length=6, resend_seconds=30, expire_minutes=10):
        code = ''.join(str(random.randint(0, 9)) for _ in range(length))
        
        now = timezone.now()
        self.otp = code
        self.created_at = now
        self.resend_after = now + timedelta(seconds=resend_seconds)
        self.expires_at = now + timedelta(minutes=expire_minutes)

        self.save(update_fields=['otp', 'created_at', 'resend_after', 'expires_at'])
        return code

    def otp_is_valid(self):
        if not self.otp or not self.expires_at:
            return False
        return timezone.now() <= self.expires_at

    def can_resend(self):
        if not self.resend_after:
            return True
        return timezone.now() >= self.resend_after

    def __str__(self):
        return f"OTP for {self.user.email} at {self.created_at}"
