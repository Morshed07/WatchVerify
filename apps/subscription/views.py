from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import status
from .models import *
from .serializers import *
from .services import *


class SubscriptionPlanApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = SubscriptionPlan.objects.filter(is_active=True)
        serializer = SubscriptionPlanSerializer(queryset, many=True)

        return Response(
            {
                "success": True,
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


class SubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all subscriptions for the authenticated user"""
        subscriptions = Subscription.objects.filter(user=request.user)
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def post(self, request):
    
        plan_id = request.data.get('plan_id')
        
        try:
            subscription = SubscriptionService.create_subscription(
                user=request.user,
                plan_id=plan_id
            )
            
            # Serialize the subscription instance
            serializer = SubscriptionSerializer(subscription)
            
            return Response({
                'success': True,
                'data': {
                    'details': serializer.data,
                    # 'payment_intent_id': intent['id'],
                    # 'client_secret': intent['client_secret'],
                    # 'amount': str(plan.price)
                }
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)