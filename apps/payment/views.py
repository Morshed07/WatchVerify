from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import InAppPurchase
from apps.subscription.models import SubscriptionPlan
from .serializers import InAppPurchaseSerializer
from .services import InAppPurchaseService


class VerifyGooglePurchaseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Verify Google Play purchase
        POST /api/purchases/verify-google/
        {
            "package_name": "com.yourapp.watchauth",
            "product_id": "monthly_premium",
            "purchase_token": "token_from_google_play"
        }
        """
        try:
            purchase, subscription = InAppPurchaseService.verify_and_activate(
                user=request.user,
                platform='google',
                purchase_data={
                    'package_name': request.data.get('package_name'),
                    'product_id': request.data.get('product_id'),
                    'purchase_token': request.data.get('purchase_token'),
                }
            )

            return Response({
                'success': True,
                'message': 'Purchase verified and subscription activated',
                'data': {
                    'purchase_id': str(purchase.id),
                    'subscription_id': str(subscription.id),
                    'subscription_type': subscription.plan.plan_type,
                    'end_date': subscription.end_date
                }
            }, status=status.HTTP_201_CREATED)

        except SubscriptionPlan.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid product_id'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class VerifyApplePurchaseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Verify Apple App Store purchase
        POST /api/purchases/verify-apple/
        {
            "receipt_data": "base64_encoded_receipt",
            "product_id": "monthly_premium"
        }
        """
        try:
            purchase, subscription = InAppPurchaseService.verify_and_activate(
                user=request.user,
                platform='apple',
                purchase_data={
                    'receipt_data': request.data.get('receipt_data'),
                    'product_id': request.data.get('product_id'),
                }
            )

            return Response({
                'success': True,
                'message': 'Purchase verified and subscription activated',
                'data': {
                    'purchase_id': str(purchase.id),
                    'subscription_id': str(subscription.id),
                    'subscription_type': subscription.plan.plan_type,
                    'end_date': subscription.end_date
                }
            }, status=status.HTTP_201_CREATED)

        except SubscriptionPlan.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid product_id'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PurchaseHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get last 20 purchases of the authenticated user
        GET /api/purchases/history/
        """
        purchases = InAppPurchase.objects.filter(user=request.user).order_by('-created_at')[:20]
        serializer = InAppPurchaseSerializer(purchases, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
