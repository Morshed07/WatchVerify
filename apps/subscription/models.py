from django.db import models
from apps.core.models import BaseModel
from datetime import timezone, timedelta
from apps.user.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.


class SubscriptionPlan(BaseModel):
    """
    Subscription plans with granular feature control
    
    Structure:
    - FREE: 3 welcome analyses
    - PAY-PER-SCAN: Standard Analysis ($2.49), Premium Analysis ($5.49)
    - PREMIUM: Monthly ($11.99), Yearly ($89.99)
    - UNLIMITED: Monthly ($19.99), Yearly ($159.99)
    """
    
    PLAN_CATEGORIES = [
        ('free', 'Free'),
        ('pay_per_scan', 'Pay Per Scan'),
        ('premium', 'Premium Subscription'),
        ('unlimited', 'Premium Unlimited'),
    ]
    
    # Basic Info
    name = models.CharField(max_length=100, help_text="Display name (e.g., 'Standard Analysis')")
    category = models.CharField(max_length=20, choices=PLAN_CATEGORIES)
    description = models.TextField(blank=True)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Duration in days for subscriptions, 0 for one-time"
    )
    scans_included = models.IntegerField(
        default=0,
        help_text="Number of scans (0 = unlimited for subscriptions)"
    )
    
    # Store IDs
    google_product_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    apple_product_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0, help_text="Display order")
    
    # ========== FEATURE FLAGS ==========
    
    # Analysis Type
    ANALYSIS_TYPES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('ultimate', 'Ultimate'),
    ]
    analysis_type = models.CharField(
        max_length=20,
        choices=ANALYSIS_TYPES,
        default='basic',
        help_text="Level of analysis detail"
    )
    
    # Core Features
    basic_authenticity_check = models.BooleanField(default=True)
    fast_processing = models.BooleanField(default=False)
    
    # Component Analysis
    show_component_breakdown = models.BooleanField(
        default=False,
        help_text="Show individual component scores (Dial, Caseback, etc.)"
    )
    show_component_observations = models.BooleanField(
        default=False,
        help_text="Show detailed observations for each component"
    )
    component_detail_level = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        help_text="0=None, 1=Scores only, 2=Scores+Brief, 3=Full details"
    )
    
    # Report Features
    show_watch_information = models.BooleanField(
        default=False,
        help_text="Show brand, model, serial number"
    )
    show_expert_notes = models.BooleanField(
        default=False,
        help_text="Show AI expert commentary"
    )
    show_confidence_metrics = models.BooleanField(
        default=False,
        help_text="Show detailed confidence scores and statistics"
    )
    
    # Export Features
    can_download_pdf = models.BooleanField(default=False)
    pdf_includes_stamps = models.BooleanField(
        default=False,
        help_text="Include official authenticity stamps in PDF"
    )
    pdf_is_bilingual = models.BooleanField(default=False)
    
    # Advanced Features
    includes_price_estimation = models.BooleanField(default=False)
    priority_processing = models.BooleanField(
        default=False,
        help_text="Skip queue for faster processing"
    )
    priority_support = models.BooleanField(default=False)
    
    # Access Control
    unlimited_analyses = models.BooleanField(
        default=False,
        help_text="No limit on number of analyses per month"
    )
    
    class Meta:
        ordering = ['category', 'sort_order', 'price']
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
    
    def __str__(self):
        return f"{self.name} (${self.price})-{self.get_category_display()}"
    
    def get_category_display_name(self):
        return dict(self.PLAN_CATEGORIES).get(self.category, "Unknown")
    
    def get_feature_summary(self):
        """Get human-readable feature list"""
        features = []
        
        # Scans
        if self.unlimited_analyses:
            features.append("Unlimited analyses")
        elif self.scans_included > 0:
            features.append(f"{self.scans_included} scan(s)")
        
        # Analysis detail
        if self.analysis_type == 'premium':
            features.append("Premium AI analysis")
        elif self.analysis_type == 'standard':
            features.append("Standard AI analysis")
        
        # Processing
        if self.fast_processing:
            features.append("Fast processing")
        if self.priority_processing:
            features.append("Priority queue")
        
        # Components
        if self.show_component_breakdown:
            features.append("Component breakdown")
        if self.show_component_observations:
            features.append("Detailed observations")
        
        # Report features
        if self.show_watch_information:
            features.append("Full watch details")
        if self.show_expert_notes:
            features.append("Expert notes")
        
        # Export
        if self.can_download_pdf:
            if self.pdf_includes_stamps:
                features.append("PDF with official stamps")
            elif self.pdf_is_bilingual:
                features.append("Bilingual PDF report")
            else:
                features.append("PDF report")
        
        # Advanced
        if self.includes_price_estimation:
            features.append("Price estimation")
        if self.priority_support:
            features.append("Priority support")
        
        return features


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

