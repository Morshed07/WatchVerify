from rest_framework import serializers
from .models import WatchAnalysis


class WatchAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchAnalysis
        fields = [
            'id', 'front_image', 'back_image', 'bracelet_image',
            'authenticity_level', 'confidence_score', 
            'brand_detected', 'model_detected', 'analysis_details',
            'status', 'processing_time', 'created_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'authenticity_level', 'confidence_score',
            'brand_detected', 'model_detected', 'analysis_details',
            'status', 'processing_time', 'completed_at'
        ]