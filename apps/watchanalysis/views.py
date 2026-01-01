from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .serializers import WatchAnalysisSerializer
from .services.watch_analysis_service import WatchAnalysisService
from .models import WatchAnalysis
from .tasks import process_watch_analysis
from .services.feature_service import FeatureService
# Create your views here.


# class WatchAnalysisAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         """
#         Create new watch analysis

#         FormData:
#             - front_image: file
#             - back_image: file
#             - bracelet_image: file
#         """

#         required_images = ['front_image', 'back_image', 'bracelet_image']
#         missing_images = [
#             img for img in required_images if img not in request.FILES
#         ]

#         if missing_images:
#             return Response(
#                 {'error': f'Missing required images: {", ".join(missing_images)}'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             analysis = WatchAnalysisService.create_analysis(
#                 user=request.user,
#                 front_img=request.FILES.get('front_image'),
#                 back_img=request.FILES.get('back_image'),
#                 bracelet_img=request.FILES.get('bracelet_image')
#             )

#             # Synchronous processing (dev / testing)
#             try:
#                 WatchAnalysisService.process_analysis(str(analysis.id))
#                 analysis.refresh_from_db()
#             except Exception:
#                 pass

#             serializer = WatchAnalysisSerializer(analysis)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)

#         except PermissionError as e:
#             return Response(
#                 {'error': str(e)},
#                 status=status.HTTP_403_FORBIDDEN
#             )
#         except Exception as e:
#             return Response(
#                 {'error': f'Analysis creation failed: {str(e)}'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
class WatchAnalysisAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        required_images = ['front_image', 'back_image', 'bracelet_image']
        missing_images = [img for img in required_images if img not in request.FILES]

        if missing_images:
            return Response(
                {'error': f'Missing required images: {", ".join(missing_images)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Create analysis record
            analysis = WatchAnalysisService.create_analysis(
                user=request.user,
                front_img=request.FILES.get('front_image'),
                back_img=request.FILES.get('back_image'),
                bracelet_img=request.FILES.get('bracelet_image')
            )

            # Asynchronous processing using Celery
            process_watch_analysis.delay(str(analysis.id))

            serializer = WatchAnalysisSerializer(analysis)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return Response(
                {'error': f'Analysis creation failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class WatchAnalysisReportAPIView(APIView):
    """Get analysis report filtered by user's plan features"""
    permission_classes = [IsAuthenticated]
    
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
        
        # Add images
        report_data['images'] = {
            'front': request.build_absolute_uri(analysis.front_image.url) if analysis.front_image else None,
            'back': request.build_absolute_uri(analysis.back_image.url) if analysis.back_image else None,
            'bracelet': request.build_absolute_uri(analysis.bracelet_image.url) if analysis.bracelet_image else None,
        }
        
        return Response(report_data)


class WatchAnalysisStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        analysis = get_object_or_404(
            WatchAnalysis,
            pk=pk,
            user=request.user
        )

        return Response({
            'id': str(analysis.id),
            'status': analysis.status,
            'created_at': analysis.created_at,
            'completed_at': analysis.completed_at,
            'error_message': (
                analysis.error_message
                if analysis.status == 'failed'
                else None
            )
        })


class WatchAnalysisHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        analyses = WatchAnalysis.objects.filter(
            user=request.user,
            status='completed'
        ).order_by('-created_at')[:20]

        serializer = WatchAnalysisSerializer(analyses, many=True)
        return Response(serializer.data)
