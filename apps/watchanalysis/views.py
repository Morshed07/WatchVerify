from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# from django.shortcuts import get_object_or_404
from .serializers import *
from .services import *
from .models import *
# Create your views here.


class WatchAnalysisAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get user's completed analysis history (last 10)
        """
        analyses = (
            WatchAnalysis.objects
            .filter(user=request.user, status='completed')
            .order_by('-created_at')[:10]
        )

        serializer = WatchAnalysisSerializer(analyses, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create new watch analysis
        """
        try:
            analysis = WatchAnalysisService.create_analysis(
                user=request.user,
                front_img=request.FILES.get('front_image'),
                back_img=request.FILES.get('back_image'),
                bracelet_img=request.FILES.get('bracelet_image')
            )

            print('#######This part of view is okay till now!!!#########')

            # Synchronous processing (testing)
            WatchAnalysisService.process_analysis(str(analysis.id))

            print('#######This 2nd part of view is okay till now!!!#########')

            serializer = WatchAnalysisSerializer(analysis)

            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        except PermissionError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)