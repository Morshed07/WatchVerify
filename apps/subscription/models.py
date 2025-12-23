from django.db import models
from apps.core.models import BaseModel
from datetime import timezone, timedelta
from apps.user.models import User

# Create your models here.


class SubscriptionPlan(BaseModel):

    PLAN_TYPES = [
        ('pay_per_scan', 'Pay Per Scan'),
        ('premium', 'Premium'),
        ('unlimited', 'Unlimited'),
    ] 
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(
        help_text="Duration in days (0 for one-time payment)",
        null=True,
        blank=True
    )
    scans_included = models.IntegerField(
        help_text="Number of scans included (0 for unlimited)",
        default=0
    )
    features = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    price_id = models.CharField(max_length=255, blank=True, null=True)

    # Store Product IDs
    google_product_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Product ID in Google Play Console"
    )
    apple_product_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Product ID in App Store Connect"
    )
    
    class Meta:
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return f"{self.name} - {self.plan_type}"


class Subscription(BaseModel): 
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    scans_remaining = models.IntegerField(default=0)
    auto_renew = models.BooleanField(default=False)
    subscription_id = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"

        db_table = 'subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"
    
    def activate(self):
        
        self.status = 'active'
        # self.start_date = timezone.now()
        
        if self.plan.duration_days:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        
        self.scans_remaining = self.plan.scans_included
        
        # Update user subscription info
        self.user.subscription_type = self.plan.plan_type
        self.user.subscription_start_date = self.start_date
        self.user.subscription_end_date = self.end_date
        self.user.is_premium = True
        self.user.free_scans_remaining = self.plan.scans_included
        self.user.save()
        self.save()
  
    def check_expiration(self):
        if self.end_date and timezone.now() > self.end_date:
            self.status = 'expired'
            self.user.subscription_type = 'free'
            self.user.is_premium = False
            self.user.save()
            self.save()

