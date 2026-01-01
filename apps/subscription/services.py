from django.db import transaction
from django.utils import timezone
from .models import SubscriptionPlan, Subscription


class SubscriptionService:
    """Handle all subscription-related business logic"""
    
    @staticmethod
    def create_subscription(user, plan_id):
        """Create a new subscription for user"""
        plan = SubscriptionPlan.objects.get(id=plan_id)
        
        with transaction.atomic():
            subscription = Subscription.objects.create(
                user=user,
                plan=plan,
                status='pending',
                start_date=timezone.now()
            )
            subscription.activate()
            return subscription
    
    @staticmethod
    def activate_subscription(subscription):
        """Activate a subscription after payment"""
        with transaction.atomic():
            subscription.activate()
            
            # Log the action
            # UsageLog.objects.create(
            #     user=subscription.user,
            #     action_type='subscription_purchased',
            #     metadata={
            #         'plan': subscription.plan.name,
            #         'amount': str(subscription.plan.price)
            #     }
            # )
    
    @staticmethod
    def cancel_subscription(subscription):
        """Cancel an active subscription"""
        with transaction.atomic():
            subscription.status = 'cancelled'
            subscription.save()
            
            # Update user
            subscription.user.subscription_type = 'free'
            subscription.user.is_premium = False
            subscription.user.save()
            
            # # Log cancellation
            # UsageLog.objects.create(
            #     user=subscription.user,
            #     action_type='subscription_cancelled',
            #     metadata={'plan': subscription.plan.name}
            # )
    
    @staticmethod
    def check_and_expire_subscriptions():
        """Cron job to check and expire subscriptions"""
        expired = Subscription.objects.filter(
            status='active',
            end_date__lt=timezone.now()
        )
        
        for subscription in expired:
            subscription.check_expiration()


# class FeatureService:
#     """Service to check feature access based on subscription"""
    
#     @staticmethod
#     def get_user_plan(user):
#         """Get user's active subscription plan"""
#         subscription = Subscription.objects.filter(
#             user=user,
#             status='active'
#         ).select_related('plan').first()
        
#         if subscription:
#             return subscription.plan
        
#         # Return free plan as default
#         return SubscriptionPlan.objects.filter(
#             category='free',
#             is_active=True
#         ).first()
    
#     @staticmethod
#     def get_report_data(analysis, user_plan):
#         """
#         Get report data filtered by plan features
        
#         Returns data structure based on what the user's plan allows them to see
#         """
#         details = analysis.analysis_details
        
#         # Base data (everyone gets this)
#         report_data = {
#             'id': str(analysis.id),
#             'status': analysis.status,
#             'analyzed_at': analysis.completed_at,
#             'processing_time': analysis.processing_time,
#             'plan_name': user_plan.name,
#             'plan_category': user_plan.category,
#         }
        
#         # Basic authenticity (all plans)
#         if user_plan.basic_authenticity_check:
#             report_data['authenticity'] = {
#                 'level': analysis.authenticity_level,
#                 'confidence_score': float(analysis.confidence_score),
#                 'verdict': details.get('conclusion', {}).get('verdict', ''),
#             }
        
#         # Watch information (Standard and above)
#         if user_plan.show_watch_information:
#             report_data['watch_information'] = {
#                 'brand': analysis.brand_detected,
#                 'model': analysis.model_detected,
#             }
            
#             # Full watch info for premium+
#             if user_plan.analysis_type in ['premium', 'ultimate']:
#                 report_data['watch_information']['serial_ref_no'] = details.get('watch', {}).get('serial_ref_no', '')
#                 report_data['watch_information']['date_of_analysis'] = details.get('watch', {}).get('date_of_analysis', '')
        
#         # Component breakdown (Premium Analysis and Premium Subscription)
#         if user_plan.show_component_breakdown:
#             component_data = {}
#             detailed_analysis = details.get('ai_response', {}).get('detailed_analysis', [])
            
#             for component in detailed_analysis:
#                 comp_name = component['component']
#                 comp_data = {
#                     'match_score': component.get('match_score', ''),
#                 }
                
#                 # Add observations based on detail level
#                 if user_plan.component_detail_level >= 2:
#                     # Brief observations
#                     obs = component.get('observations', '')
#                     comp_data['observations'] = obs[:200] + '...' if len(obs) > 200 else obs
                
#                 if user_plan.component_detail_level >= 3:
#                     # Full observations
#                     comp_data['observations'] = component.get('observations', '')
                
#                 component_data[comp_name] = comp_data
            
#             report_data['components'] = component_data
#             report_data['component_scores'] = details.get('component_scores', {})
        
#         # Confidence metrics and statistics (Premium Analysis+)
#         if user_plan.show_confidence_metrics:
#             report_data['statistics'] = {
#                 'average_component_score': details.get('average_component_score', 0),
#                 'passed_components': [k for k, v in details.get('component_status', {}).items() if v == 'pass'],
#                 'failed_components': [k for k, v in details.get('component_status', {}).items() if v == 'fail'],
#                 'total_components_analyzed': len(details.get('component_scores', {})),
#             }
#             report_data['component_status'] = details.get('component_status', {})
        
#         # Expert notes (Premium Analysis+)
#         if user_plan.show_expert_notes:
#             report_data['expert_note'] = details.get('conclusion', {}).get('expert_note', '')
#             report_data['conclusion'] = details.get('conclusion', {})
        
#         # Report ID and metadata (Premium+)
#         if user_plan.analysis_type in ['premium', 'ultimate']:
#             report_data['report_id'] = details.get('report', {}).get('report_id', f'AWC-{analysis.id}')
#             report_data['date_of_issue'] = details.get('report', {}).get('date_of_issue', '')
        
#         # Price estimation (Unlimited only)
#         if user_plan.includes_price_estimation:
#             report_data['price_estimation'] = {
#                 'estimated_value': None,  # TODO: Implement
#                 'currency': 'USD',
#                 'confidence': None,
#                 'message': 'Price estimation available for this watch'
#             }
        
#         # PDF export info
#         if user_plan.can_download_pdf:
#             report_data['pdf_available'] = True
#             report_data['pdf_features'] = {
#                 'includes_stamps': user_plan.pdf_includes_stamps,
#                 'is_bilingual': user_plan.pdf_is_bilingual,
#             }
        
#         # Add upgrade prompts for limited plans
#         upgrade_suggestions = []
#         if not user_plan.show_component_breakdown:
#             upgrade_suggestions.append("Upgrade to Premium Analysis to see detailed component breakdown")
#         if not user_plan.show_expert_notes:
#             upgrade_suggestions.append("Upgrade to see expert AI commentary")
#         if not user_plan.can_download_pdf:
#             upgrade_suggestions.append("Upgrade to download PDF reports")
#         if not user_plan.includes_price_estimation:
#             upgrade_suggestions.append("Upgrade to Premium Unlimited for price estimation")
        
#         if upgrade_suggestions:
#             report_data['upgrade_suggestions'] = upgrade_suggestions
        
#         return report_data