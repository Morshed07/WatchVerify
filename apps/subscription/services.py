from django.db import transaction
from django.utils import timezone
from decimal import Decimal
# import stripe
import uuid
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


