from django.urls import path
from .views import (
    WatchAnalysisAPIView,
    WatchAnalysisReportAPIView,
    WatchAnalysisStatusAPIView,
    WatchAnalysisHistoryAPIView,
)

urlpatterns = [
    path('analyses/', WatchAnalysisAPIView.as_view()),
    path('analyses/history/', WatchAnalysisHistoryAPIView.as_view()),
    path('analyses/<uuid:pk>/report/', WatchAnalysisReportAPIView.as_view()),
    path('analyses/<uuid:pk>/status/', WatchAnalysisStatusAPIView.as_view()),
]
