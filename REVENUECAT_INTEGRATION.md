# RevenueCat Integration Guide

## Overview
RevenueCat is a cross-platform subscription management service that simplifies in-app purchase verification for iOS, Android, and web. This integration replaces manual Google Play and Apple App Store verification with RevenueCat's unified API.

## Setup Steps

### 1. Create RevenueCat Account
1. Go to https://www.revenuecat.com
2. Sign up for a free account
3. Create a new project
4. Add your app (iOS and/or Android)

### 2. Get API Keys
1. In RevenueCat dashboard, go to **Project Settings**
2. Navigate to **API Keys** section
3. Copy your **Public API Key** (used for requests)
4. Copy your **Secret Key** (used for webhooks)

### 3. Configure Environment Variables
Add to your `.env` file:
```
REVENUECAT_API_KEY=your_public_api_key
REVENUECAT_SECRET_KEY=your_secret_key
```

Or update directly in `chronoverify/settings.py` if using hardcoded values (not recommended for production).

### 4. Create Database Migration
The model already has RevenueCat fields, but you need to run migrations:

```bash
python manage.py makemigrations payment
python manage.py migrate payment
```

### 5. Configure Product IDs in RevenueCat
In your RevenueCat dashboard:

1. **Configure Entitlements** (optional, but recommended):
   - Go to Products → Entitlements
   - Create entitlements (e.g., "premium", "unlimited")
   
2. **Map Products**:
   - For each subscription plan in Django, ensure the Google Product ID and Apple Product ID match RevenueCat's configuration
   - Example: If your Django plan has `google_product_id="premium_monthly"`, configure this in RevenueCat with the exact same ID

### 6. Configure Webhooks
1. In RevenueCat dashboard, go to **Project Settings → Webhooks**
2. Click **Add Webhook**
3. Set webhook URL to: `https://yourdomain.com/api/webhooks/revenuecat/`
4. Select events to receive:
   - `PURCHASE` - When a user makes a purchase
   - `CANCELLATION` - When a subscription is cancelled
   - `EXPIRATION` - When a subscription expires
   - `RENEWAL` - When a subscription renews
5. Copy the **Signing Secret** and add to your `.env` as `REVENUECAT_SECRET_KEY`

### 7. Install Dependencies
```bash
pip install requests
```

It's likely already installed, but verify it's in your `requirements.txt`.

---

## API Usage

### Client-Side (Mobile App)

On iOS/Android, use RevenueCat SDK:

**iOS (Swift)**:
```swift
import RevenueCat

// Initialize RevenueCat
Purchases.logLevel = .debug
Purchases.configure(withAPIKey: "your_public_api_key")

// Get offerings
Purchases.shared.offerings { (offerings, error) in
    if let offering = offerings?.current {
        // Display packages to user
    }
}

// Make purchase
Purchases.shared.purchase(package: package) { (transaction, info, error, cancelled) in
    // Purchase completed - backend will receive webhook
}
```

**Android (Kotlin)**:
```kotlin
import com.revenuecat.purchases.Purchases
import com.revenuecat.purchases.LogLevel

// Initialize RevenueCat
Purchases.logLevel = LogLevel.DEBUG
Purchases.configure(Purchases.PurchasesConfiguration.Builder(context, "your_public_api_key").build())

// Get offerings
Purchases.sharedInstance.getOfferings({ offerings ->
    val offering = offerings?.current
    // Display packages to user
}, { error ->
    // Handle error
})

// Make purchase
Purchases.sharedInstance.purchase(activity, package) { product, customerInfo ->
    // Purchase completed - backend will receive webhook
}
```

### Backend - Verify Purchase

**Endpoint**: `POST /api/purchases/revenuecat-verify/`

**Request**:
```json
{
    "platform": "apple",
    "product_id": "premium_monthly",
    "receipt_data": "base64_encoded_receipt"
}
```

For Android:
```json
{
    "platform": "google",
    "product_id": "premium_monthly",
    "purchase_token": "token_from_google_play"
}
```

**Response**:
```json
{
    "success": true,
    "message": "Purchase verified with RevenueCat and subscription activated",
    "data": {
        "purchase_id": "uuid",
        "subscription_id": "uuid",
        "plan": "Premium Monthly",
        "price": "11.99",
        "end_date": "2025-03-04T12:00:00Z",
        "rc_transaction_id": "rc_transaction_id"
    }
}
```

---

## Webhook Events

Your backend automatically handles these webhook events:

### PURCHASE Event
Triggered when a user makes a purchase or renews their subscription.
- Creates `InAppPurchase` record
- Creates/Updates `Subscription` record
- Activates subscription
- Updates user as premium

### CANCELLATION Event
Triggered when a user cancels their subscription.
- Updates purchase status to "cancelled"
- Marks subscription as "cancelled"
- Sets user as non-premium

### EXPIRATION Event
Triggered when a subscription expires naturally.
- Updates purchase status to "expired"
- Marks subscription as "expired"
- Sets user as non-premium

### RENEWAL Event
Triggered when a subscription auto-renews.
- Updates purchase status to "verified"
- Updates subscription expiration date
- Keeps user premium

---

## Key Model Fields

### InAppPurchase
New RevenueCat-specific fields:
- `rc_transaction_id` - Unique transaction ID from RevenueCat
- `rc_customer_id` - Customer ID in RevenueCat (mapped to Django user ID)
- `rc_entitlement_id` - Entitlement ID if using RevenueCat entitlements
- `raw_response` - Full RevenueCat response data

### Subscription
Already supported, just needs to be created via RevenueCat service.

---

## Testing

### 1. Test Webhook (Development)
Use RevenueCat's webhook testing tool in the dashboard to send test events.

### 2. Test API Endpoint
```bash
curl -X POST http://localhost:8000/api/purchases/revenuecat-verify/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "apple",
    "product_id": "premium_monthly",
    "receipt_data": "test_receipt_data"
  }'
```

### 3. Monitor Logs
RevenueCat logs are available in both RevenueCat dashboard and your Django logs.

---

## Common Issues

### 1. "RevenueCat API keys not configured"
**Solution**: Make sure `REVENUECAT_API_KEY` and `REVENUECAT_SECRET_KEY` are in your `.env` file.

### 2. Invalid Product ID
**Solution**: Ensure your Django subscription plan's `google_product_id` or `apple_product_id` matches exactly what's configured in RevenueCat.

### 3. Webhook Signature Invalid
**Solution**: Verify that `REVENUECAT_SECRET_KEY` in your settings matches the signing secret in RevenueCat dashboard.

### 4. User Not Found in Webhook
**Solution**: RevenueCat webhook uses `app_user_id` mapped to Django user ID. Make sure you're using Django's `user.id` as the app user ID on the mobile app.

---

## Migration from Manual Verification

If you were previously using manual Google Play/Apple verification:

1. Keep old endpoints working for existing code
2. Gradually migrate users to RevenueCat
3. Store RevenueCat transaction ID for all new purchases
4. Eventually deprecate old endpoints

Old endpoints still available:
- `POST /api/purchases/verify-google/`
- `POST /api/purchases/verify-apple/`

---

## RevenueCat Dashboard Features

Use the dashboard to:
- Monitor subscription metrics
- View customer lifecycle
- Test webhooks
- Configure entitlements
- Set up offering prices
- View analytics and reports

---

## References

- [RevenueCat Documentation](https://docs.revenuecat.com)
- [RevenueCat API Reference](https://docs.revenuecat.com/docs/api-reference)
- [RevenueCat Webhooks](https://docs.revenuecat.com/docs/server-side-api#webhooks)
- [RevenueCat SDKs](https://docs.revenuecat.com/docs/getting-started)
