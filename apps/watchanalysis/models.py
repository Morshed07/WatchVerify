from django.db import models
from apps.core.models import BaseModel
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.user.models import User



class WatchAnalysis(BaseModel):
    
    AUTHENTICITY_LEVELS = [
        ('original', 'Original'),
        ('similar', 'Similar to Original'),
        ('fake', 'Fake'),
        ('inconclusive', 'Inconclusive'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analyses')
    
    front_image = models.ImageField(upload_to='watches/front/%Y/%m/')
    back_image = models.ImageField(upload_to='watches/back/%Y/%m/')
    bracelet_image = models.ImageField(upload_to='watches/bracelet/%Y/%m/')
    
    # Analysis Results
    authenticity_level = models.CharField(
        max_length=20, 
        choices=AUTHENTICITY_LEVELS,
        null=True,
        blank=True
    )
    confidence_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Confidence percentage (0-100)",
        null=True,
        blank=True
    )
    
    brand_detected = models.CharField(max_length=100, blank=True)
    model_detected = models.CharField(max_length=100, blank=True)
    
    # Analysis Details JSON
    analysis_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed AI analysis results including all metrics"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    # Processing Info
    processing_time = models.FloatField(null=True, blank=True, help_text="Time in seconds")
    error_message = models.TextField(blank=True)
    
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Watch Analysis'
        verbose_name_plural = 'Watch analyses'
        db_table = 'watch_analyses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['authenticity_level']),
        ]
    
    def __str__(self):
        return f"Analysis {self.id} - {self.user.email} - {self.status}"
    

class UsageLog(BaseModel):
    
    ACTION_TYPES = [
        ('scan', 'Watch Scan'),
        ('subscription_purchased', 'Subscription Purchased'),
        ('subscription_renewed', 'Subscription Renewed'),
        ('subscription_cancelled', 'Subscription Cancelled'),
        ('login', 'User Login'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_logs')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    analysis = models.ForeignKey(
        WatchAnalysis,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Usage Log'
        verbose_name_plural = 'Usage Logs'
        db_table = 'usage_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.action_type} - {self.created_at}"
