from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import *


class WatchAnalysisService:
    """Handle watch analysis logic"""
    
    @staticmethod
    def can_user_analyze(user):
        """Check if user has permission to analyze"""
        if not user.can_scan:
            if user.subscription_type == 'free':
                return False, "Free scans exhausted. Please upgrade."
            else:
                return False, "Subscription expired. Please renew."
        return True, "OK"
    
    @staticmethod
    def create_analysis(user, front_img, back_img, bracelet_img):
        """Create new watch analysis"""
        can_analyze, message = WatchAnalysisService.can_user_analyze(user)
        
        if not can_analyze:
            raise PermissionError(message)
        
        with transaction.atomic():
            analysis = WatchAnalysis.objects.create(
                user=user,
                front_image=front_img,
                back_image=back_img,
                bracelet_image=bracelet_img,
                status='pending'
            )
            
            # Decrement scans
            if user.subscription_type == 'free':
                user.decrement_free_scans()
            
            user.total_scans_used += 1
            user.save(update_fields=['total_scans_used'])
            
            # Log usage
            UsageLog.objects.create(
                user=user,
                action_type='scan',
                analysis=analysis
            )
            
            return analysis
    
    @staticmethod
    def process_analysis(analysis_id):
        """Process watch analysis with AI (to be called by Celery)"""
        analysis = WatchAnalysis.objects.get(id=analysis_id)
        analysis.status = 'processing'
        analysis.save()
        print('########service 1st part########')
        try:
            # TODO: Call your AI model here
            # result = ai_model.analyze(
            #     front=analysis.front_image,
            #     back=analysis.back_image,
            #     bracelet=analysis.bracelet_image
            # )
            
            # Simulated AI response
            result = {
                'authenticity': 'original',
                'confidence': 87.5,
                'brand': 'Rolex',
                'model': 'Submariner',
                'details': {
                    'dial_analysis': 'Consistent with original',
                    'bracelet_quality': 'High quality',
                    'movement': 'Appears genuine'
                }
            }
            print(result)
            analysis.authenticity_level = result['authenticity']
            analysis.confidence_score = Decimal(str(result['confidence']))
            analysis.brand_detected = result.get('brand', '')
            analysis.model_detected = result.get('model', '')
            analysis.analysis_details = result.get('details', {})
            analysis.status = 'completed'
            analysis.completed_at = timezone.now()
            analysis.save()
            
        except Exception as e:
            analysis.status = 'failed'
            analysis.error_message = str(e)
            analysis.save()