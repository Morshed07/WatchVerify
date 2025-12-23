import requests
from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
from apps.subscription.models import *
from apps.subscription.services import *
from .models import *


class GooglePlayService:
    """Handle Google Play In-App Purchase verification"""
    
    @staticmethod
    def verify_purchase(package_name, product_id, purchase_token):
        """
        Verify Google Play purchase
        
        Setup Required:
        1. Go to Google Cloud Console
        2. Create Service Account
        3. Download JSON key
        4. Grant access in Google Play Console
        """
        try:
            # Load credentials
            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_SERVICE_ACCOUNT_FILE,
                scopes=['https://www.googleapis.com/auth/androidpublisher']
            )
            
            # Build service
            service = build('androidpublisher', 'v3', credentials=credentials)
            
            # Verify subscription or product purchase
            if product_id.endswith('_subscription'):
                # Subscription purchase
                result = service.purchases().subscriptions().get(
                    packageName=package_name,
                    subscriptionId=product_id,
                    token=purchase_token
                ).execute()
            else:
                # One-time purchase
                result = service.purchases().products().get(
                    packageName=package_name,
                    productId=product_id,
                    token=purchase_token
                ).execute()
            
            return {
                'valid': True,
                'data': result,
                'order_id': result.get('orderId'),
                'purchase_time': result.get('startTimeMillis') or result.get('purchaseTimeMillis'),
                'expiry_time': result.get('expiryTimeMillis'),
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    @staticmethod
    def acknowledge_purchase(package_name, product_id, purchase_token):
        """Acknowledge purchase (required by Google)"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_SERVICE_ACCOUNT_FILE,
                scopes=['https://www.googleapis.com/auth/androidpublisher']
            )
            
            service = build('androidpublisher', 'v3', credentials=credentials)
            
            service.purchases().products().acknowledge(
                packageName=package_name,
                productId=product_id,
                token=purchase_token,
                body={}
            ).execute()
            
            return True
        except Exception as e:
            print(f"Acknowledgment error: {e}")
            return False


class AppleAppStoreService:
    """Handle Apple App Store In-App Purchase verification"""
    
    # Apple endpoints
    PRODUCTION_URL = 'https://buy.itunes.apple.com/verifyReceipt'
    SANDBOX_URL = 'https://sandbox.itunes.apple.com/verifyReceipt'
    
    @staticmethod
    def verify_receipt(receipt_data, exclude_old_transactions=True):
        """
        Verify Apple receipt
        
        Setup Required:
        1. Get Shared Secret from App Store Connect
        2. Add to settings.py
        """
        payload = {
            'receipt-data': receipt_data,
            'password': settings.APPLE_SHARED_SECRET,
            'exclude-old-transactions': exclude_old_transactions
        }
        
        # Try production first
        response = requests.post(
            AppleAppStoreService.PRODUCTION_URL,
            json=payload,
            timeout=30
        )
        
        result = response.json()
        
        # If status 21007, it's a sandbox receipt
        if result.get('status') == 21007:
            response = requests.post(
                AppleAppStoreService.SANDBOX_URL,
                json=payload,
                timeout=30
            )
            result = response.json()
        
        # Status 0 means valid
        if result.get('status') == 0:
            receipt_info = result.get('receipt', {})
            latest_receipt_info = result.get('latest_receipt_info', [])
            
            return {
                'valid': True,
                'data': result,
                'receipt_info': receipt_info,
                'latest_receipt_info': latest_receipt_info,
                'transaction_id': latest_receipt_info[0].get('transaction_id') if latest_receipt_info else None,
                'original_transaction_id': latest_receipt_info[0].get('original_transaction_id') if latest_receipt_info else None,
            }
        else:
            return {
                'valid': False,
                'error': f"Status code: {result.get('status')}",
                'data': result
            }


class InAppPurchaseService:
    """Unified service for handling IAP from both platforms"""
    
    @staticmethod
    def verify_and_activate(user, platform, purchase_data):
        """
        Verify purchase and activate subscription
        
        purchase_data format:
        
        For Google:
        {
            'package_name': 'com.yourapp.watchauth',
            'product_id': 'monthly_premium',
            'purchase_token': 'token_from_google'
        }
        
        For Apple:
        {
            'receipt_data': 'base64_receipt_from_apple',
            'product_id': 'monthly_premium'
        }
        """
        
        # Verify based on platform
        if platform == 'google':
            verification = GooglePlayService.verify_purchase(
                package_name=purchase_data.get('package_name'),
                product_id=purchase_data.get('product_id'),
                purchase_token=purchase_data.get('purchase_token')
            )
        elif platform == 'apple':
            verification = AppleAppStoreService.verify_receipt(
                receipt_data=purchase_data.get('receipt_data')
            )
        else:
            raise ValueError("Invalid platform")
        
        if not verification.get('valid'):
            raise Exception(f"Purchase verification failed: {verification.get('error')}")
        
        # Find the plan by product_id
        product_id = purchase_data.get('product_id')
        if platform == 'google':
            plan = SubscriptionPlan.objects.get(google_product_id=product_id, is_active=True)
        else:
            plan = SubscriptionPlan.objects.get(apple_product_id=product_id, is_active=True)
        
        # Create purchase record
        with transaction.atomic():
            purchase = InAppPurchase.objects.create(
                user=user,
                plan=plan,  # ← MANDATORY: Link to the plan
                platform=platform,
                product_id=product_id,
                status='verified',
                is_verified=True,
                verified_at=timezone.now(),
                raw_response=verification.get('data', {})
            )
            
            # Platform-specific fields
            if platform == 'google':
                purchase.google_order_id = verification.get('order_id')
                purchase.google_purchase_token = purchase_data.get('purchase_token')
                purchase.google_product_id = product_id
                purchase.google_package_name = purchase_data.get('package_name')
                
                # Acknowledge purchase
                GooglePlayService.acknowledge_purchase(
                    purchase_data.get('package_name'),
                    product_id,
                    purchase_data.get('purchase_token')
                )
            else:
                purchase.apple_transaction_id = verification.get('transaction_id')
                purchase.apple_original_transaction_id = verification.get('original_transaction_id')
                purchase.apple_receipt_data = purchase_data.get('receipt_data')
                purchase.apple_product_id = product_id
            
            purchase.save()
            
            # Create and activate subscription
            subscription = SubscriptionService.create_and_activate_subscription(
                user=user,
                plan_id=plan.id
            )
            
            # Link purchase to subscription
            purchase.subscription = subscription
            purchase.save()
            
            return purchase, subscription