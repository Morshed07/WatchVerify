# RevenueCat Quick Start Guide

## 5-Minute Setup

### Step 1: Get API Keys (2 min)
1. Go to https://www.revenuecat.com
2. Sign up → Create project
3. Go to **Project Settings → API Keys**
4. Copy **Public API Key** and **Secret Key**

### Step 2: Configure Environment (1 min)
Add to `.env`:
```
REVENUECAT_API_KEY=pk_your_key_here
REVENUECAT_SECRET_KEY=sk_your_key_here
```

### Step 3: Run Migration (1 min)
```bash
python manage.py migrate payment
```

### Step 4: Configure Webhook (1 min)
1. In RevenueCat, go to **Project Settings → Webhooks**
2. Click **Add Webhook**
3. URL: `https://yourdomain.com/api/webhooks/revenuecat/`
4. Copy signing secret → add to `.env` as `REVENUECAT_SECRET_KEY`

### ✅ Done! 
Backend is ready to receive purchases.

---

## Test It

### Test Webhook
1. In RevenueCat, click **Test Event**
2. Check Django logs for webhook processing
3. Look for "Webhook processed" message

### Test Verify Endpoint
```bash
curl -X POST http://localhost:8000/api/purchases/revenuecat-verify/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "apple",
    "product_id": "premium_monthly",
    "receipt_data": "test"
  }'
```

---

## For Mobile Developers

See [MOBILE_INTEGRATION_GUIDE.md](MOBILE_INTEGRATION_GUIDE.md) for iOS/Android code.

Key points:
- Initialize RevenueCat SDK with same API key
- Handle purchases with RevenueCat SDK
- Backend receives webhook events automatically
- Check user entitlements in app

---

## File Reference

| File | Purpose |
|------|---------|
| `revenuecat_service.py` | Core RevenueCat logic |
| `webhook.py` | Handle webhook events |
| `REVENUECAT_INTEGRATION.md` | Complete guide |
| `MOBILE_INTEGRATION_GUIDE.md` | iOS/Android code |

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/purchases/revenuecat-verify/` | POST | Verify purchase |
| `/api/webhooks/revenuecat/` | POST | Receive events |

---

## Webhook Events Auto-Handled

✅ **PURCHASE** → Create subscription, activate user  
✅ **RENEWAL** → Update subscription dates  
✅ **CANCELLATION** → Mark subscription cancelled  
✅ **EXPIRATION** → Mark subscription expired  

No additional code needed!

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "API keys not configured" | Check `.env` file |
| "Invalid product ID" | Verify product ID matches RevenueCat |
| "Webhook signature invalid" | Check secret key matches |
| "User not found" | Ensure user ID matches app_user_id |

---

## Next Steps

1. ✅ Add API keys
2. ✅ Run migration
3. ✅ Set up webhook
4. ⏭️ Integrate SDK in iOS app (see MOBILE_INTEGRATION_GUIDE.md)
5. ⏭️ Integrate SDK in Android app (see MOBILE_INTEGRATION_GUIDE.md)
6. ⏭️ Test with real purchases
7. ⏭️ Deploy to production

---

## Support

- RevenueCat Docs: https://docs.revenuecat.com
- RevenueCat Dashboard: https://app.revenuecat.com
- Check Django logs: `apps.payment.revenuecat_service`
