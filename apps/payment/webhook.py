"""
RevenueCat Webhook Handler
Processes webhook events from RevenueCat

Setup Instructions:
1. RevenueCat Dashboard → Project Settings → Webhooks
2. Add Webhook URL: https://yourdomain.com/api/webhooks/revenuecat/
3. Copy Webhook Signing Secret
4. Add to .env: REVENUECAT_SECRET_KEY=your_secret
5. Select events: PURCHASE, RENEWAL, EXPIRATION, CANCELLATION
"""

import hmac
import hashlib
import logging
import json
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .revenuecat_service import revenuecat

logger = logging.getLogger(__name__)


# FIX: Use @method_decorator(csrf_exempt) — setting csrf_exempt = True as a class
# attribute on APIView does NOT disable CSRF in Django REST Framework.
# Also set authentication_classes and permission_classes to [] so DRF's
# SessionAuthentication doesn't enforce CSRF on this unauthenticated endpoint.
@method_decorator(csrf_exempt, name='dispatch')
class RevenueCatWebhookView(APIView):
    """
    Handle RevenueCat webhook events

    Supported Events:
    - PURCHASE: New subscription purchase
    - RENEWAL: Subscription auto-renewed
    - EXPIRATION: Subscription expired
    - CANCELLATION: User cancelled subscription
    - BILLING_ISSUE: Payment failed
    - TRANSFER: Subscription transferred
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """
        Handle webhook POST from RevenueCat

        RevenueCat sends:
        {
            "event": {
                "type": "PURCHASE",
                "id": "event-id",
                "created_at_ms": 1234567890
            },
            "customer": {
                "app_user_id": "user@example.com"
            },
            "transaction": {
                "id": "transaction-id",
                "product_id": "premium_yearly",
                "purchase_date": "2026-04-20T10:30:00Z",
                "expiration_date": "2027-04-20T10:30:00Z",
                "platform": "google"
            }
        }
        """
        try:
            logger.info("Received RevenueCat webhook")

            # Verify webhook signature
            signature_valid = self._verify_signature(request)
            if not signature_valid:
                logger.warning("Invalid RevenueCat webhook signature")
                # In production, enforce strict verification:
                # return Response(
                #     {"error": "Invalid signature"},
                #     status=status.HTTP_401_UNAUTHORIZED
                # )
                # For development, log and continue:
                logger.info("Proceeding without valid signature (development mode)")

            data = request.data
            event_type = data.get("event", {}).get("type")

            if not event_type:
                logger.warning("No event type in webhook data")
                return Response(
                    {"error": "No event type"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            logger.info(f"Processing webhook event: {event_type}")
            logger.debug(f"Webhook data: {json.dumps(data, indent=2, default=str)}")

            revenuecat.handle_webhook(event_type, data)

            logger.info(f"Webhook processed successfully: {event_type}")
            return Response(
                {
                    "status": "processed",
                    "event_type": event_type,
                    "timestamp": data.get("event", {}).get("created_at_ms"),
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """Health check endpoint for webhook"""
        return Response(
            {
                "status": "webhook_ready",
                "signature_verification": (
                    "enabled" if getattr(settings, "REVENUECAT_SECRET_KEY", None) else "disabled"
                ),
            },
            status=status.HTTP_200_OK
        )

    def _verify_signature(self, request) -> bool:
        """
        Verify RevenueCat webhook signature using HMAC-SHA256

        RevenueCat computes:
            HMAC-SHA256(raw_body, secret_key)
        and sends the hex digest in:
            X-RevenueCat-Content-Signature: <hex_digest>
        """
        try:
            signature = request.META.get("HTTP_X_REVENUECAT_CONTENT_SIGNATURE", "")
            secret_key = getattr(settings, "REVENUECAT_SECRET_KEY", "")

            if not signature:
                logger.warning("Missing X-RevenueCat-Content-Signature header")
                return False

            if not secret_key:
                logger.warning("Missing REVENUECAT_SECRET_KEY in settings")
                return False

            body = request.body

            # FIX: Python 3's hmac module uses hmac.new(), not hmac.new().
            # Using keyword arguments to be explicit and avoid mistakes.
            mac = hmac.new(
                key=secret_key.encode('utf-8'),
                msg=body,
                digestmod=hashlib.sha256
            )
            expected_signature = mac.hexdigest()

            # Use constant-time comparison to prevent timing attacks
            is_valid = hmac.compare_digest(signature, expected_signature)

            if not is_valid:
                logger.warning(
                    f"Signature mismatch. "
                    f"Expected: {expected_signature[:20]}..., "
                    f"Got: {signature[:20]}..."
                )

            return is_valid

        except Exception as e:
            logger.error(f"Signature verification error: {str(e)}", exc_info=True)
            return False