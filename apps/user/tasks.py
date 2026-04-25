from celery import shared_task
from django.utils import timezone
from django.db import models
from datetime import timedelta
from apps.user.models import User
import logging

logger = logging.getLogger(__name__)


@shared_task
def grant_free_scans_to_users():
    """
    Grant 1 free scan to all free tier users every 3 days.
    This task should be scheduled to run every 3 days using Celery Beat.
    """
    try:
        # Get all free tier users
        free_users = User.objects.filter(subscription_type='free')
        
        updated_count = 0
        
        for user in free_users:
            # Add 1 scan to free_scans_remaining
            user.free_scans_remaining += 1
            user.save()
            updated_count += 1
            
            logger.info(
                f"Granted 1 free scan to user {user.email}. "
                f"Total remaining scans: {user.free_scans_remaining}"
            )
        
        logger.info(f"Successfully granted free scans to {updated_count} users")
        return {
            'status': 'success',
            'message': f'Granted 1 free scan to {updated_count} free tier users',
            'updated_users': updated_count
        }
        
    except Exception as e:
        logger.error(f"Error granting free scans to users: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task
def grant_free_scans_to_users_bulk():
    """
    Bulk version - Grant 1 free scan to all free tier users every 3 days.
    More efficient for large number of users.
    """
    try:
        # Update all free tier users in a single query
        updated_count = User.objects.filter(
            subscription_type='free'
        ).update(
            free_scans_remaining=models.F('free_scans_remaining') + 1
        )
        
        logger.info(f"Successfully granted free scans to {updated_count} users (bulk update)")
        return {
            'status': 'success',
            'message': f'Granted 1 free scan to {updated_count} free tier users',
            'updated_users': updated_count
        }
        
    except Exception as e:
        logger.error(f"Error granting free scans to users: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task
def downgrade_expired_subscriptions():
    """
    Downgrade users with expired subscriptions back to free tier.
    This task should be scheduled to run daily using Celery Beat.
    - Sets subscription_type to 'free'
    - Sets is_premium to False
    - Resets free_scans_remaining to 3
    """
    try:
        # Find users with expired subscriptions (not free tier)
        expired_subscriptions = User.objects.filter(
            subscription_end_date__lt=timezone.now()
        ).exclude(
            subscription_type='free'
        )
        
        updated_count = expired_subscriptions.count()
        
        if updated_count > 0:
            # Bulk update expired subscriptions
            expired_subscriptions.update(
                subscription_type='free',
                is_premium=False,
                # free_scans_remaining=1
            )
            
            logger.info(
                f"Downgraded {updated_count} users with expired subscriptions to free tier"
            )
        
        return {
            'status': 'success',
            'message': f'Downgraded {updated_count} users with expired subscriptions to free tier',
            'downgraded_users': updated_count
        }
        
    except Exception as e:
        logger.error(f"Error downgrading expired subscriptions: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e)
        }
