from django.urls import path
from .views import (
    WatchAnalysisAPIView,
    WatchAnalysisReportAPIView,
    WatchAnalysisStatusAPIView,
    WatchAnalysisHistoryAPIView,
    WatchAnalysisDetailAPIView
)

urlpatterns = [
    path('analyses/', WatchAnalysisAPIView.as_view()),
    path('analyses/history/', WatchAnalysisHistoryAPIView.as_view()),
    path('analyses/<uuid:pk>/', WatchAnalysisDetailAPIView.as_view()),
    path('analyses/report/<uuid:pk>/', WatchAnalysisReportAPIView.as_view()),
    path('analyses/<uuid:pk>/status/', WatchAnalysisStatusAPIView.as_view()),
]
