from django.urls import path
from .views import *

urlpatterns = [
    path('purchases/verify-google/', VerifyGooglePurchaseAPIView.as_view(), name='verify-google-purchase'),
    path('purchases/verify-apple/', VerifyApplePurchaseAPIView.as_view(), name='verify-apple-purchase'),
    path('purchases/history/', PurchaseHistoryAPIView.as_view(), name='purchase-history'),
]