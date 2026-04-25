from rest_framework import serializers
from .models import WatchAnalysis


class WatchAnalysisSerializer(serializers.ModelSerializer):
    # Make boolean fields explicitly settable with defaults
    original_box = serializers.BooleanField(required=False, default=False)
    original_brand_certificate = serializers.BooleanField(required=False, default=False)
    invoice = serializers.BooleanField(required=False, default=False)
    
    class Meta:
        model = WatchAnalysis
        fields = [
            'id', 'front_image', 'back_image', 'bracelet_image',
            'authenticity_level', 'confidence_score', 
            'brand_detected', 'model_detected', 'analysis_details',
            'analysis_report_id', 'status', 'processing_time',  
            'original_box', 'original_brand_certificate',
            'invoice', 'created_at',
            'completed_at',
        ]
        read_only_fields = [
            'id', 'authenticity_level', 'confidence_score',
            'brand_detected', 'model_detected', 'analysis_details',
            'analysis_report_id', 'status', 'processing_time', 'completed_at'
        ]


class WatchAnalysisHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchAnalysis
        fields = [
            'id', 'brand_detected',
            'model_detected',
            'confidence_score',
            'created_at'
        ]
        read_only_fields = fields