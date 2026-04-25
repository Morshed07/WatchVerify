from django.urls import path
from .views import *
from .webhook import RevenueCatWebhookView

urlpatterns = [
    path('purchases/history/', PurchaseHistoryAPIView.as_view(), name='purchase-history'),

    # RevenueCat endpoints
    path('purchases/revenuecat-verify/', RevenueCatVerifyPurchaseAPIView.as_view(), name='revenuecat-verify-purchase'),
    path('webhooks/revenuecat/', RevenueCatWebhookView.as_view(), name='revenuecat-webhook'),
]