from celery import shared_task
from .services import WatchAnalysisService
from django.utils import timezone
from apps.user.models import User
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_watch_analysis(self, analysis_id):
    """
    Background task to process watch analysis
    
    Usage:
        from .tasks import process_watch_analysis
        process_watch_analysis.delay(str(analysis_id))
    """
    try:
        WatchAnalysisService.process_analysis(analysis_id)
        logger.info(f"Successfully processed analysis {analysis_id}")
        
    except Exception as e:
        logger.error(f"Failed to process analysis {analysis_id}: {str(e)}")
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task
def update_expired_premium_subscriptions():
    """
    Periodic task to check and update is_premium status for users with expired subscriptions.
    Call this task periodically (e.g., every hour) using Celery Beat.
    
    Usage in celery.py:
        app.conf.beat_schedule = {
            'update-expired-premium': {
                'task': 'apps.watchanalysis.tasks.update_expired_premium_subscriptions',
                'schedule': crontab(minute=0),  # Every hour
            },
        }
    """
    try:
        # Get all users with is_premium=True and expired subscription_end_date
        expired_premium_users = User.objects.filter(
            is_premium=True,
            subscription_end_date__lt=timezone.now()
        )
        
        updated_count = 0
        for user in expired_premium_users:
            user.is_premium = False
            user.save(update_fields=['is_premium'])
            updated_count += 1
        
        logger.info(f"Updated {updated_count} users - set is_premium to False for expired subscriptions")
        return {"updated_count": updated_count}
        
    except Exception as e:
        logger.error(f"Error updating expired premium subscriptions: {str(e)}")
        raise
