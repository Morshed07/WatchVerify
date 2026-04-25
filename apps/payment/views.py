from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging

from .models import InAppPurchase
from .serializers import InAppPurchaseSerializer
from .revenuecat_service import revenuecat
from django.utils import timezone
            

logger = logging.getLogger(__name__)


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


class RevenueCatVerifyPurchaseAPIView(APIView):
    """
    POST /api/purchases/revenuecat-verify/
 
    Called by the mobile app immediately after a purchase to get fast
    feedback. Does NOT verify the purchase itself — RevenueCat's webhook
    already did that. This endpoint only reads state from your own DB.
 
    Priority order:
      1. If user.is_premium is already True  → return active (webhook already ran)
      2. If an active InAppPurchase exists   → return active
      3. If RevenueCat API confirms active   → return active
      4. Otherwise                           → return pending (webhook en route)
    """
 
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        try:
            platform = request.data.get('platform', '').lower()
            product_id = request.data.get('product_id', '').strip()
 
            if not platform or platform not in ['apple', 'google']:
                return Response(
                    {
                        'success': False,
                        'error': 'platform must be "apple" or "google"',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
 
            if not product_id:
                return Response(
                    {
                        'success': False,
                        'error': 'product_id is required',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
 
            user = request.user
 
            # ── Step 1: Check our own DB first (cheapest, fastest) ──────────
            # If the webhook already fired, user.is_premium is True.
            user.refresh_from_db()
            if user.is_premium:
                logger.info(f"User {user.email} already premium — returning active")
                return Response(
                    {
                        'success': True,
                        'status': 'active',
                        'message': 'Subscription is active',
                        'verification_method': 'local_db',
                    },
                    status=status.HTTP_200_OK
                )

            # ── Step 2: Check for a verified InAppPurchase record ───────────
            active_purchase = (
                InAppPurchase.objects
                .filter(
                    user=user,
                    platform=platform,
                    product_id=product_id,
                    status='verified',
                    is_verified=True,
                )
                .filter(
                    # Either no expiry (lifetime) or expiry in the future
                    expiry_date__isnull=True
                )
                .first()
                or
                InAppPurchase.objects
                .filter(
                    user=user,
                    platform=platform,
                    product_id=product_id,
                    status='verified',
                    is_verified=True,
                    expiry_date__gt=timezone.now(),
                )
                .first()
            )
 
            if active_purchase:
                logger.info(f"Active InAppPurchase found for {user.email}")
                return Response(
                    {
                        'success': True,
                        'status': 'active',
                        'message': 'Subscription is active',
                        'expires_at': (
                            active_purchase.expiry_date.isoformat()
                            if active_purchase.expiry_date else None
                        ),
                        'verification_method': 'local_db',
                    },
                    status=status.HTTP_200_OK
                )
 
            # ── Step 3: Optional RevenueCat API check ───────────────────────
            # Only runs if webhook hasn't fired yet (rare — usually < 5 sec delay)
            try:
                rc_response = revenuecat.verify_purchase(
                    user=user,
                    platform=platform,
                    product_id=product_id,
                )
 
                rc_status = rc_response.get('status')
 
                if rc_status == 'active':
                    logger.info(f"RevenueCat API confirms active for {user.email}")
                    return Response(
                        {
                            'success': True,
                            'status': 'active',
                            'message': 'Subscription confirmed by RevenueCat',
                            'expires_at': rc_response.get('expires_at'),
                            'verification_method': 'revenuecat_api',
                        },
                        status=status.HTTP_200_OK
                    )
 
                # pending / waiting / timeout / no_api_key — all mean the
                # webhook hasn't confirmed yet; tell the frontend to poll
                logger.info(
                    f"RevenueCat status '{rc_status}' for {user.email} — webhook pending"
                )
 
            except Exception as api_err:
                # RC API is optional — log and fall through to pending
                logger.warning(
                    f"RevenueCat API check failed for {user.email}: {api_err}"
                )
 
            # ── Step 4: Webhook hasn't arrived yet ──────────────────────────
            # Tell the frontend to poll /api/user/me/ every 2 seconds.
            return Response(
                {
                    'success': True,
                    'status': 'pending',
                    'message': (
                        'Purchase received. Waiting for RevenueCat to confirm. '
                        'Please poll /api/user/me/ — is_premium will become true '
                        'within a few seconds.'
                    ),
                    'verification_method': 'webhook_pending',
                    'poll_endpoint': '/api/user/me/',
                    'poll_interval_ms': 2000,
                    'max_polls': 10,
                },
                status=status.HTTP_202_ACCEPTED
            )
 
        except Exception as e:
            logger.error(
                f"Unexpected error in RevenueCatVerifyPurchaseAPIView: {e}",
                exc_info=True
            )
            return Response(
                {
                    'success': False,
                    'error': 'Internal server error during purchase verification',
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


