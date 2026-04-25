import os
from celery import Celery
from celery.schedules import crontab
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chronoverify.settings')

app = Celery('chronoverify')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'update-expired-premium': {
        'task': 'apps.watchanalysis.tasks.update_expired_premium_subscriptions',
        'schedule': crontab(minute=0),  # every hour at minute 0
    },
    'grant-free-scans': {
        'task': 'apps.user.tasks.grant_free_scans_to_users_bulk',
        'schedule': timedelta(days=3),  # ✅ every 3 days (exact)
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
