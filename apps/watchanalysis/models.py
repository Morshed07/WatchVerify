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
    
    @property
    def report_id(self):
        '''Get report ID from analysis details'''
        return self.analysis_details.get('report', {}).get('report_id', f'AWC-{self.id}')
    
    @property
    def serial_number(self):
        '''Get watch serial number'''
        return self.analysis_details.get('watch', {}).get('serial_ref_no', '')
    
    @property
    def verdict(self):
        '''Get authenticity verdict'''
        return self.analysis_details.get('conclusion', {}).get('verdict', '')
    
    @property
    def expert_note(self):
        '''Get expert note from conclusion'''
        return self.analysis_details.get('conclusion', {}).get('expert_note', '')
    
    @property
    def component_scores(self):
        '''Get all component scores as dict'''
        return self.analysis_details.get('component_scores', {})
    
    @property
    def average_component_score(self):
        '''Get average score across all components'''
        return self.analysis_details.get('average_component_score', 0)
    
    @property
    def passed_components(self):
        '''Get list of components that passed (score >= 70%)'''
        component_status = self.analysis_details.get('component_status', {})
        return [comp for comp, status in component_status.items() if status == 'pass']
    
    @property
    def failed_components(self):
        '''Get list of components that failed (score < 70%)'''
        component_status = self.analysis_details.get('component_status', {})
        return [comp for comp, status in component_status.items() if status == 'fail']
    
    def get_component_details(self, component_name):
        '''Get detailed analysis for a specific component'''
        return self.analysis_details.get('components', {}).get(component_name, {})
    
    def get_full_report(self):
        '''Get complete formatted report data'''
        if self.status != 'completed':
            return None
        
        return {
            'report_id': self.report_id,
            'status': self.status,
            'analyzed_at': self.completed_at.isoformat() if self.completed_at else None,
            'processing_time': self.processing_time,
            
            'watch_information': {
                'brand': self.brand_detected,
                'model': self.model_detected,
                'serial_number': self.serial_number,
            },
            
            'authenticity_assessment': {
                'level': self.authenticity_level,
                'confidence_score': float(self.confidence_score),
                'verdict': self.verdict,
                'expert_note': self.expert_note,
            },
            
            'component_analysis': self.analysis_details.get('components', {}),
            'component_scores': self.component_scores,
            'average_component_score': self.average_component_score,
            
            'summary': {
                'passed_components': self.passed_components,
                'failed_components': self.failed_components,
                'total_components_analyzed': len(self.component_scores),
            },
            
            'images': {
                'front': self.front_image.url if self.front_image else None,
                'back': self.back_image.url if self.back_image else None,
                'bracelet': self.bracelet_image.url if self.bracelet_image else None,
            }
        }

    
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

    