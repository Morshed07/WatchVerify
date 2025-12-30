from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from ..models import *
from apps.subscription.models import Subscription
from .ai_service import WatchAIAnalyzer
import logging
import time
import json
logger = logging.getLogger(__name__)


class WatchAnalysisService:
    """Handle watch analysis logic"""
    
    @staticmethod
    def can_user_analyze(user):
        # Check subscription status
        if user.subscription_type == 'free':
            # Free users: check free scans remaining
            if user.free_scans_remaining > 0:
                return True, "OK"
            else:
                return False, "Free scans exhausted. Please upgrade to continue."
        
        elif user.subscription_type == 'pay_per_scan':
            # Pay-per-scan: check if active subscription has scans remaining
            active_sub = Subscription.objects.filter(
                user=user,
                status='active'
            ).first()
            
            if not active_sub:
                return False, "No active subscription. Please purchase a scan."
            
            if active_sub.scans_remaining > 0:
                return True, "OK"
            else:
                return False, "Pay-per-scan used. Please purchase another scan."
            
        elif user.subscription_type == 'premium':
            # Premium: check if subscription is active (not expired)
            active_sub = Subscription.objects.filter(
                user=user,
                status='active'
            ).first()
            
            if not active_sub:
                return False, "No active subscription. Please purchase a plan."
            
            if active_sub.scans_remaining > 0:
                return True, "OK"
            else:
                return False, "Premium plan used fully. Please purchase another scan."
            
        
        elif user.subscription_type == 'unlimited':
            # Unlimited: check if subscription is active (not expired)
            if user.is_subscription_active:
                return True, "OK"
            else:
                return False, "Subscription expired. Please renew your subscription."
        
        else:
            # Unknown subscription type
            return False, "Invalid subscription type. Please contact support."
    
    @staticmethod
    def create_analysis(user, front_img, back_img, bracelet_img):
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
            
            # Decrement scans based on subscription type
            if user.subscription_type == 'free':
                # Free users: decrement from user's free_scans_remaining
                user.decrement_free_scans()
                
            elif user.subscription_type == 'pay_per_scan':
                # Pay-per-scan: decrement from subscription's scans_remaining
                active_sub = Subscription.objects.filter(
                    user=user,
                    status='active'
                ).first()
                if active_sub and active_sub.scans_remaining > 0:
                    active_sub.scans_remaining -= 1
                    active_sub.save()
                    user.decrement_scans()  # Also decrement free scans if any
                    user.save()

            elif user.subscription_type == 'premium':
                # Premium users: decrement from subscription's scans_remaining
                active_sub = Subscription.objects.filter(
                    user=user,
                    status='active'
                ).first()
                if active_sub and active_sub.scans_remaining > 0:
                    active_sub.scans_remaining -= 1
                    active_sub.save()
                    user.decrement_scans()  # Also decrement free scans if any
                    user.save()

            elif user.subscription_type == 'unlimited':
                # Unlimited users: No decrement needed - unlimited scans
                # Just verify subscription is active (already checked in can_user_analyze)
                pass
            
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
        """Process watch analysis with AI"""
        analysis = WatchAnalysis.objects.get(id=analysis_id)
        analysis.status = 'processing'
        analysis.save()
        
        start_time = time.time()
        
        try:
            # Initialize AI analyzer
            ai_analyzer = WatchAIAnalyzer()
            
            # Run AI analysis
            logger.info(f"Starting AI analysis for {analysis_id}")
            ai_result = ai_analyzer.analyze_watch(
                front_image=analysis.front_image,
                back_image=analysis.back_image,
                bracelet_image=analysis.bracelet_image
            )
            
            # DEBUG: Log the raw AI result
            logger.info(f"AI Result received: {json.dumps(ai_result, indent=2)}")
            
            # Extract key information from AI result
            watch_info = ai_result.get('watch_information', {})
            conclusion = ai_result.get('conclusion', {})
            detailed_analysis = ai_result.get('detailed_analysis', [])
            price_estimation = ai_result.get("price_estimation", {})


            # DEBUG: Log extracted data
            logger.info(f"Watch Info: {watch_info}")
            logger.info(f"Conclusion: {conclusion}")
            logger.info(f"Detailed Analysis Count: {len(detailed_analysis)}")
            
            # Parse authenticity score (handle both "87%" and "87" formats)
            authenticity_score_str = conclusion.get('overall_authenticity_score', '0%')
            authenticity_score = float(str(authenticity_score_str).replace('%', '').strip())
            
            # Determine authenticity level based on score and verdict
            verdict = conclusion.get('verdict', '').lower()
            if verdict == 'authentic' or authenticity_score >= 85:
                authenticity_level = 'original'
            elif verdict == 'counterfeit' or authenticity_score < 50:
                authenticity_level = 'fake'
            elif verdict == 'uncertain' or 50 <= authenticity_score < 85:
                authenticity_level = 'similar'
            else:
                authenticity_level = 'inconclusive'
          
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Build comprehensive analysis details with all essential data
            comprehensive_details = {
                # Original AI Response (complete)
                'ai_response': ai_result,
                
                # Report Metadata
                'report': {
                    'report_id': ai_result.get('report_id', f'AWC-{analysis.id}'),
                    'date_of_issue': ai_result.get('date_of_issue', ''),
                    'processing_time_seconds': processing_time,
                    'analyzed_at': timezone.now().isoformat(),
                },
                
                # Watch Information (easily accessible)
                'watch': {
                    'brand': watch_info.get('brand', ''),
                    'model': watch_info.get('model', ''),
                    'serial_ref_no': watch_info.get('serial_ref_no', ''),
                    'date_of_analysis': watch_info.get('date_of_analysis', ''),
                },
                
                # Component Analysis (all components with scores)
                'components': {
                    component['component']: {
                        'match_score': component.get('match_score', ''),
                        'observations': component.get('observations', ''),
                        'score_numeric': float(component.get('match_score', '0%').replace('%', '').strip()) if component.get('match_score') else 0
                    }
                    for component in detailed_analysis
                },
                
                # Conclusion (summary)
                'conclusion': {
                    'verdict': conclusion.get('verdict', ''),
                    'overall_score': authenticity_score,
                    'authenticity_level': authenticity_level,
                    'expert_note': conclusion.get('expert_note', ''),
                },
                # -------------------------
                # 💰 PRICE ESTIMATION (AI ONLY)
                # -------------------------
                "price_estimation": {
                    "estimated_price": price_estimation.get("estimated_price", "Unavailable"),
                    "currency": price_estimation.get("currency", "USD"),
                    "condition_assumed": price_estimation.get("condition_assumed"),
                    "confidence_level": price_estimation.get("confidence_level"),
                    "notes": price_estimation.get("notes"),
                },
                # Component Scores Summary (for quick access)
                'component_scores': {
                    component['component']: component.get('match_score', '')
                    for component in detailed_analysis
                },
                
                # Average Component Score (calculated)
                'average_component_score': sum([
                    float(comp.get('match_score', '0%').replace('%', '').strip())
                    for comp in detailed_analysis if comp.get('match_score')
                ]) / len(detailed_analysis) if detailed_analysis else 0,
                
                # Pass/Fail by Component (for UI)
                'component_status': {
                    component['component']: 'pass' if float(component.get('match_score', '0%').replace('%', '').strip()) >= 70 else 'fail'
                    for component in detailed_analysis if component.get('match_score')
                },
            }
            # DEBUG: Log comprehensive details before saving
            logger.info(f"Comprehensive details prepared. Keys: {list(comprehensive_details.keys())}")
            
            # Update analysis record with ALL essential data
            analysis.authenticity_level = authenticity_level
            analysis.confidence_score = Decimal(str(authenticity_score))
            analysis.brand_detected = watch_info.get('brand', '').strip()
            analysis.model_detected = watch_info.get('model', '').strip()
            analysis.analysis_details = comprehensive_details  # Store enhanced comprehensive data
            analysis.status = 'completed'
            analysis.processing_time = processing_time
            analysis.estimated_price = price_estimation.get("estimated_price", "Unavailable")
            analysis.completed_at = timezone.now()
            
            # Save with explicit update_fields to ensure JSON is saved
            analysis.save(update_fields=[
                'authenticity_level',
                'confidence_score',
                'brand_detected',
                'model_detected',
                'analysis_details',
                'status',
                'processing_time',
                'completed_at',
                'estimated_price',
            ])
            
            # Verify save
            analysis.refresh_from_db()
            logger.info(f"Analysis saved. analysis_details keys: {list(analysis.analysis_details.keys())}")
            logger.info(f"Analysis {analysis_id} completed: {authenticity_level} ({authenticity_score}%) - {analysis.brand_detected} {analysis.model_detected}")
            
        except json.JSONDecodeError as e:
            processing_time = time.time() - start_time
            error_msg = f"JSON parsing error: {str(e)}"
            logger.error(f"Analysis {analysis_id} - {error_msg}")
            
            analysis.status = 'failed'
            analysis.error_message = error_msg
            analysis.processing_time = processing_time
            analysis.save(update_fields=['status', 'error_message', 'processing_time'])
            raise
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Processing error: {str(e)}"
            logger.error(f"Analysis {analysis_id} - {error_msg}")
            logger.exception("Full traceback:")
            
            analysis.status = 'failed'
            analysis.error_message = error_msg
            analysis.processing_time = processing_time
            analysis.save(update_fields=['status', 'error_message', 'processing_time'])
            raise

