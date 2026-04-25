from django.urls import path
from .views import PrivacyPolicyView

urlpatterns = [
    path('', PrivacyPolicyView, name='privacy-policy'),
]
