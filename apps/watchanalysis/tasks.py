from celery import shared_task
from .services import WatchAnalysisService
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
