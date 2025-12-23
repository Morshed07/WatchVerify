# ============================================================================
# MODELS - Add to your existing models.py
# ============================================================================

from django.db import models
from apps.core.models import BaseModel
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.subscription.models import Subscription, SubscriptionPlan

User = get_user_model()


class InAppPurchase(BaseModel):

    PLATFORM_CHOICES = [
        ('google', 'Google Play'),
        ('apple', 'Apple App Store'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='purchases',
        help_text="The subscription plan that was purchased"
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchases'
    )
    
    # Platform info
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    
    # Google Play fields
    google_order_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    google_purchase_token = models.TextField(blank=True, null=True)
    google_product_id = models.CharField(max_length=255, blank=True, null=True)
    google_package_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Apple App Store fields
    apple_transaction_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    apple_original_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    apple_receipt_data = models.TextField(blank=True, null=True)
    apple_product_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Common fields
    product_id = models.CharField(max_length=255, help_text="Product ID from store")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    purchase_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    # Raw response from store
    raw_response = models.JSONField(default=dict, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'In App Purchase'
        verbose_name_plural = 'In App Purchases'
        db_table = 'in_app_purchases'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['platform', 'status']),
            models.Index(fields=['google_order_id']),
            models.Index(fields=['apple_transaction_id']),
        ]
    
    def __str__(self):
        return f"{self.platform} - {self.user.email} - {self.product_id}"