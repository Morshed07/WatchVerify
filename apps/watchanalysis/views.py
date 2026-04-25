from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from django.shortcuts import get_object_or_404
from .serializers import (
    WatchAnalysisSerializer,
    WatchAnalysisHistorySerializer
)
from .services.watch_analysis_service import WatchAnalysisService
from .models import WatchAnalysis
from .tasks import process_watch_analysis
from .services.feature_service import FeatureService
import logging

logger = logging.getLogger(__name__)


def parse_boolean_field(value, field_name, default=False):
    """
    Safely parse a value to boolean with comprehensive error handling.
    
    Args:
        value: The value to parse (can be bool, str, None, int, etc.)
        field_name: Name of the field (for logging)
        default: Default value if parsing fails
    
    Returns:
        Boolean value
    """
    if value is None:
        logger.debug(f"{field_name}: None received, using default {default}")
        return default
    
    # Already a boolean
    if isinstance(value, bool):
        return value
    
    # String values
    if isinstance(value, str):
        normalized = value.lower().strip()
        if normalized in ('true', '1', 'yes', 'on'):
            return True
        elif normalized in ('false', '0', 'no', 'off', ''):
            return False
        else:
            logger.warning(f"{field_name}: Invalid string value '{value}', using default {default}")
            return default
    
    # Integer values (0 = False, non-zero = True)
    if isinstance(value, int):
        return bool(value)
    
    # Fallback for unexpected types
    logger.warning(f"{field_name}: Unexpected type {type(value).__name__}, using default {default}")
    return default


def parse_string_field(value, field_name, default="", max_length=None):
    """
    Safely parse a value to string with validation.
    
    Args:
        value: The value to parse
        field_name: Name of the field (for logging)
        default: Default value if parsing fails
        max_length: Maximum allowed string length
    
    Returns:
        String value
    """
    if value is None:
        logger.debug(f"{field_name}: None received, using default '{default}'")
        return default
    
    # Convert to string
    str_value = str(value).strip() if value else default
    
    # Check max length
    if max_length and len(str_value) > max_length:
        logger.warning(f"{field_name}: String exceeds max length {max_length}, truncating")
        str_value = str_value[:max_length]
    
    return str_value


def parse_integer_field(value, field_name, default=0, min_value=None, max_value=None):
    """
    Safely parse a value to integer with validation.
    
    Args:
        value: The value to parse
        field_name: Name of the field (for logging)
        default: Default value if parsing fails
        min_value: Minimum allowed value
        max_value: Maximum allowed value
    
    Returns:
        Integer value
    """
    if value is None:
        logger.debug(f"{field_name}: None received, using default {default}")
        return default
    
    try:
        int_value = int(value)
        
        # Validate range
        if min_value is not None and int_value < min_value:
            logger.warning(f"{field_name}: Value {int_value} below minimum {min_value}, using {min_value}")
            return min_value
        
        if max_value is not None and int_value > max_value:
            logger.warning(f"{field_name}: Value {int_value} exceeds maximum {max_value}, using {max_value}")
            return max_value
        
        return int_value
    except (ValueError, TypeError):
        logger.warning(f"{field_name}: Cannot parse '{value}' to integer, using default {default}")
        return default


class WatchAnalysisAPIView(APIView):
    permission_classes = [IsAuthenticated]
    # Support multiple content types
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def post(self, request):
        """
        Create new watch analysis with multi-format support.
        
        Supports:
        - multipart/form-data (file uploads with fields)
        - application/x-www-form-urlencoded (form fields)
        - application/json (JSON payload)
        """
        
        required_images = ['front_image', 'back_image', 'bracelet_image']
        missing_images = [img for img in required_images if img not in request.FILES]

        if missing_images:
            logger.warning(f"Missing images for {request.user.email}: {missing_images}")
            return Response(
                {'error': f'Missing required images: {", ".join(missing_images)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Parse boolean fields safely with defaults
            original_box = parse_boolean_field(
                request.data.get('original_box'),
                'original_box',
                default=False
            )
            original_brand_certificate = parse_boolean_field(
                request.data.get('original_brand_certificate'),
                'original_brand_certificate',
                default=False
            )
            invoice = parse_boolean_field(
                request.data.get('invoice'),
                'invoice',
                default=False
            )
            
            # Parse optional string fields
            language = parse_string_field(
                request.data.get('language'),
                'language',
                default=request.user.language_preference,
                max_length=20
            )
            
            # Log parsed request data
            logger.info(
                f"Watch analysis request from {request.user.email}: "
                f"content_type={request.content_type}, "
                f"original_box={original_box}, "
                f"original_brand_certificate={original_brand_certificate}, "
                f"invoice={invoice}, "
                f"language={language}"
            )
            
            # Create analysis record
            analysis = WatchAnalysisService.create_analysis(
                user=request.user,
                front_img=request.FILES.get('front_image'),
                back_img=request.FILES.get('back_image'),
                bracelet_img=request.FILES.get('bracelet_image'),
                language=language,
                original_box=original_box,
                original_brand_certificate=original_brand_certificate,
                invoice=invoice
            )

            # Asynchronous processing using Celery
            process_watch_analysis.delay(str(analysis.id))

            serializer = WatchAnalysisSerializer(analysis)
            logger.info(f"Watch analysis {analysis.id} created successfully for {request.user.email}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except PermissionError as e:
            logger.warning(f"Permission denied for {request.user.email}: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            logger.error(f"Validation error for {request.user.email}: {str(e)}")
            return Response(
                {'error': f'Validation error: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Analysis creation failed for {request.user.email}: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Analysis creation failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class WatchAnalysisReportAPIView(APIView):
    """Get analysis report filtered by user's plan features"""
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def get(self, request, pk):
        analysis = get_object_or_404(
            WatchAnalysis,
            id=pk,
            user=request.user
        )
        
        # Check status
        if analysis.status in ['pending', 'processing']:
            return Response({
                'status': analysis.status,
                'message': f'Analysis is {analysis.status}. Please check back shortly.'
            })
        
        if analysis.status == 'failed':
            return Response({
                'status': 'failed',
                'error': analysis.error_message
            })
        
        # Get user's plan
        user_plan = FeatureService.get_user_plan(request.user)
        
        # Get filtered report data based on plan
        report_data = FeatureService.get_report_data(analysis, user_plan)
        
        def get_clean_url(image_field):
            if not image_field:
                return None
            url = request.build_absolute_uri(image_field.url)
            return url.replace(':8000', '')
        # Add images
        report_data['images'] = {
            'front': get_clean_url(analysis.front_image),
            'back': get_clean_url(analysis.back_image),
            'bracelet': get_clean_url(analysis.bracelet_image),
        }
        
        # Add certificate and documentation fields
        report_data['certificate_and_documentation'] = {
            'original_box': analysis.original_box,
            'original_brand_certificate': analysis.original_brand_certificate,
            'invoice': analysis.invoice,
        }
        
        # Add report metadata
        report_data['created_at'] = analysis.created_at.isoformat() if analysis.created_at else None
        report_data['completed_at'] = analysis.completed_at.isoformat() if analysis.completed_at else None
        
        return Response(report_data)


class WatchAnalysisStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request, pk):
        analysis = get_object_or_404(
            WatchAnalysis,
            pk=pk,
            user=request.user
        )

        return Response({
            'id': str(analysis.id),
            'status': analysis.status,
            'report_id': analysis.analysis_report_id,
            'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
            'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None,
            'error_message': (
                analysis.error_message
                if analysis.status == 'failed'
                else None
            )
        })


class WatchAnalysisHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request):
        analyses = WatchAnalysis.objects.filter(
            user=request.user,
            status='completed'
        ).order_by('-created_at')[:20]

        serializer = WatchAnalysisHistorySerializer(analyses, many=True)
        return Response(serializer.data)


class WatchAnalysisDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request, pk):
        analysis = get_object_or_404(
            WatchAnalysis,
            pk=pk,
            user=request.user
        )

        serializer = WatchAnalysisSerializer(analysis)
        return Response(serializer.data)
