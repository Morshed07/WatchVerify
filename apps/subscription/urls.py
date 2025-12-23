from django.urls import path
from .views import *


urlpatterns = [
    path('list/', SubscriptionPlanApiView.as_view(), name='subscription-list'),
    path('subscribe/', SubscriptionAPIView.as_view(), name='subscription'),
]
