from rest_framework import serializers
from .models import SubscriptionPlan, Subscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'plan_details', 'status',
            'start_date', 'end_date', 'scans_remaining',
            'auto_renew', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'start_date', 'end_date']