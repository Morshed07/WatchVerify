from django.urls import path
from .views import *


urlpatterns = [
    path('analysis-report/', WatchAnalysisAPIView.as_view(), name='watch-analysis-report')
]
