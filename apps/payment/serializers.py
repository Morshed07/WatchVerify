from rest_framework import serializers
from .models import *

class InAppPurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = InAppPurchase
        fields = [
            'id', 'platform', 'product_id', 'status',
            'purchase_date', 'expiry_date', 'is_verified',
            'created_at'
        ]
        read_only_fields = ['id', 'status', 'is_verified']