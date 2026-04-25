"""
RevenueCat Integration Service - FINAL VERSION
Fixes: INITIAL_PURCHASE event, real RC webhook payload structure,
       platform normalisation, customer ID extraction
"""

import requests
import logging
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from datetime import datetime
from typing import Optional, Dict, Any
from apps.user.models import User
from apps.subscription.models import Subscription, SubscriptionPlan
from apps.subscription.services import SubscriptionService
from .models import InAppPurchase

logger = logging.getLogger(__name__)


def _normalise_platform(raw: str) -> str:
    mapping = {
        "play_store": "google", "android": "google",
        "google": "google",     "amazon": "google",
        "app_store": "apple",   "ios": "apple",
        "apple": "apple",       "macos": "apple",
    }
    return mapping.get((raw or "").lower(), "google")


def _ms_to_iso(ms) -> Optional[str]:
    if ms is None:
        return None
    try:
        return datetime.utcfromtimestamp(int(ms) / 1000).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None


def _parse_date(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


class RevenueCatService:

    BASE_URL = "https://api.revenuecat.com/v1"

    PURCHASE_EVENTS = {
        "INITIAL_PURCHASE",
        "PURCHASE",
        "RENEWAL",
        "PRODUCT_CHANGE",
        "UNCANCELLATION",
    }
    CANCELLATION_EVENTS = {"CANCELLATION", "SUBSCRIBER_ALIAS"}
    EXPIRATION_EVENTS = {"EXPIRATION"}
    BILLING_ISSUE_EVENTS = {"BILLING_ISSUE"}

    def __init__(self):
        self.api_key = getattr(settings, 'REVENUECAT_API_KEY', None)
        self.secret_key = getattr(settings, 'REVENUECAT_SECRET_KEY', None)
        if not self.api_key:
            logger.warning("REVENUECAT_API_KEY not configured")
        if not self.secret_key:
            logger.warning("REVENUECAT_SECRET_KEY not configured")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _extract_customer_id(self, data: Dict[str, Any]) -> Optional[str]:
        """
        RevenueCat real webhooks put app_user_id inside event{}.
        Postman test payloads put it inside customer{}.
        Check both.
        """
        event = data.get("event", {})
        cid = event.get("app_user_id")
        if cid:
            return cid

        customer = data.get("customer", {})
        cid = customer.get("app_user_id")
        if cid:
            return cid

        aliases = event.get("aliases", [])
        if aliases:
            return aliases[0]

        return None

    def _extract_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Real RC webhooks: transaction fields are inside event{}.
        Postman test payloads: explicit transaction{} key.
        Handle both.
        """
        if "transaction" in data:
            return data["transaction"]

        event = data.get("event", {})
        return {
            "id": event.get("id"),
            "product_id": event.get("product_id"),
            "platform": _normalise_platform(event.get("store", "")),
            "purchase_date": _ms_to_iso(event.get("purchased_at_ms")),
            "expiration_date": _ms_to_iso(event.get("expiration_at_ms")),
            "entitlement_id": (event.get("entitlement_ids") or [None])[0],
        }

    def handle_webhook(self, event_type: str, data: Dict[str, Any]) -> None:
        try:
            rc_customer_id = self._extract_customer_id(data)

            if not rc_customer_id:
                logger.warning("No customer ID found in webhook payload")
                logger.debug(f"Top-level keys: {list(data.keys())}")
                logger.debug(f"event keys: {list(data.get('event', {}).keys())}")
                return

            logger.info(f"Webhook customer_id: {rc_customer_id}")

            user = None
            try:
                user = User.objects.get(email=rc_customer_id)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(id=rc_customer_id)
                except (User.DoesNotExist, ValueError):
                    logger.warning(f"No user found for: {rc_customer_id}")
                    return

            logger.info(f"Matched user: {user.email}")

            if event_type in self.PURCHASE_EVENTS:
                self._handle_purchase_event(user, data)
            elif event_type in self.CANCELLATION_EVENTS:
                self._handle_cancellation_event(user, data)
            elif event_type in self.EXPIRATION_EVENTS:
                self._handle_expiration_event(user, data)
            elif event_type in self.BILLING_ISSUE_EVENTS:
                logger.warning(f"Billing issue for {user.email}")
            else:
                logger.info(f"Unhandled event type: {event_type}")

        except Exception as e:
            logger.error(f"Webhook dispatch failed: {e}", exc_info=True)

    def _handle_purchase_event(self, user: User, data: Dict[str, Any]) -> None:
        transaction = self._extract_transaction(data)
        product_id = transaction.get("product_id")
        platform = _normalise_platform(transaction.get("platform", ""))

        logger.info(f"Purchase event | user={user.email} product_id={product_id} platform={platform}")

        if not product_id:
            logger.error("product_id missing — cannot match SubscriptionPlan")
            return

        try:
            try:
                plan = SubscriptionPlan.objects.get(
                    Q(google_product_id=product_id) | Q(apple_product_id=product_id)
                )
                logger.info(f"Plan matched: {plan.name}")
            except SubscriptionPlan.DoesNotExist:
                available = []
                for p in SubscriptionPlan.objects.all():
                    if p.google_product_id:
                        available.append(f"google:{p.google_product_id}")
                    if p.apple_product_id:
                        available.append(f"apple:{p.apple_product_id}")
                logger.error(
                    f"No plan for product_id='{product_id}'. "
                    f"DB has: {', '.join(available) or 'NONE'}"
                )
                return

            purchase_date = _parse_date(transaction.get("purchase_date"))
            expiry_date = _parse_date(transaction.get("expiration_date"))
            rc_txn_id = transaction.get("id")

            subscription, sub_created = Subscription.objects.get_or_create(
                user=user,
                plan=plan,
                defaults={
                    "status": "pending",
                    "start_date": purchase_date or timezone.now(),
                    "auto_renew": True,
                }
            )
            logger.info(f"Subscription {'created' if sub_created else 'found'}: {subscription.id}")

            purchase, p_created = InAppPurchase.objects.update_or_create(
                rc_transaction_id=rc_txn_id,
                defaults={
                    "user": user,
                    "plan": plan,
                    "subscription": subscription,
                    "platform": platform,
                    "product_id": product_id,
                    "status": "verified",
                    "is_verified": True,
                    "verified_at": timezone.now(),
                    "purchase_date": purchase_date or timezone.now(),
                    "expiry_date": expiry_date,
                    "rc_customer_id": user.email,
                    "rc_entitlement_id": transaction.get("entitlement_id"),
                    "raw_response": data,
                }
            )
            logger.info(f"InAppPurchase {'created' if p_created else 'updated'}: {purchase.id}")

            SubscriptionService.activate_subscription(subscription)
            user.refresh_from_db()
            logger.info(f"✅ Purchase done | {user.email} | plan={plan.name} | is_premium={user.is_premium}")

        except Exception as e:
            logger.error(f"❌ Purchase processing error: {e}", exc_info=True)

    def _handle_cancellation_event(self, user: User, data: Dict[str, Any]) -> None:
        transaction = self._extract_transaction(data)
        rc_txn_id = transaction.get("id")
        try:
            purchase = InAppPurchase.objects.get(rc_transaction_id=rc_txn_id)
            purchase.status = "cancelled"
            purchase.save()
            if purchase.subscription:
                SubscriptionService.cancel_subscription(purchase.subscription)
            logger.info(f"Cancelled: {user.email}")
        except InAppPurchase.DoesNotExist:
            logger.warning(f"No purchase for cancellation txn: {rc_txn_id}")

    def _handle_expiration_event(self, user: User, data: Dict[str, Any]) -> None:
        transaction = self._extract_transaction(data)
        rc_txn_id = transaction.get("id")
        try:
            purchase = InAppPurchase.objects.get(rc_transaction_id=rc_txn_id)
            purchase.status = "expired"
            purchase.save()
            if purchase.subscription:
                SubscriptionService.cancel_subscription(purchase.subscription)
            logger.info(f"Expired: {user.email}")
        except InAppPurchase.DoesNotExist:
            logger.warning(f"No purchase for expiration txn: {rc_txn_id}")

    def verify_purchase(self, user: User, platform: str, product_id: str, **kwargs) -> Dict[str, Any]:
        if not self.api_key:
            return {"status": "pending", "message": "No API key — waiting for webhook"}
        try:
            url = f"{self.BASE_URL}/subscribers/{user.email}"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 404:
                return {"status": "waiting"}
            response.raise_for_status()
            subs = response.json().get("subscriber", {}).get("subscriptions", {})
            for _, sub in subs.items():
                if sub.get("product_identifier") == product_id:
                    expires = sub.get("expires_date")
                    if expires:
                        exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
                        if exp_dt > timezone.now():
                            return {"status": "active", "product_id": product_id, "expires_at": expires}
            return {"status": "no_subscription"}
        except Exception as e:
            logger.warning(f"RC API check failed: {e}")
            return {"status": "error", "message": str(e)}


revenuecat = RevenueCatService()